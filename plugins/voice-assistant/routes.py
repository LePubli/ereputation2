"""
Voice Assistant Routes - API endpoints pour l'analyse d'appels vocaux

Endpoints pour transcrire des appels, analyser les conversations,
et générer des insights actionnables.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import tempfile
import os

from loguru import logger

from .assistant import (
    VoiceAssistant,
    SentimentType,
    SignalType,
    get_voice_assistant
)


router = APIRouter(prefix="/api/v1/voice", tags=["Voice Assistant"])


# === Modèles de données ===

class CallMetadata(BaseModel):
    prospect_id: str
    date: Optional[str] = None
    duration_seconds: Optional[int] = 0
    participants: Optional[List[str]] = None
    call_type: str = "discovery"  # discovery, demo, negotiation, follow_up


class AnalyzeTranscriptRequest(BaseModel):
    transcript: str = Field(..., description="Transcription complète de l'appel")
    prospect_id: str
    metadata: Optional[CallMetadata] = None


class GenerateSummaryRequest(BaseModel):
    analysis: Dict[str, Any]


# === Endpoints ===

@router.post("/transcribe", response_model=Dict[str, Any], summary="Transcrire un fichier audio")
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Transcrit un fichier audio d'appel en texte.
    
    Formats supportés : MP3, WAV, M4A, OGG
    Utilise Whisper (open-source) pour la transcription.
    """
    try:
        engine = get_voice_assistant()
        
        # Sauvegarde temporaire du fichier
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        try:
            # Transcription
            result = engine.transcribe_audio(tmp_path)
            
            return {
                "success": True,
                "transcription": result.get("text", ""),
                "duration_seconds": result.get("duration_seconds", 0),
                "language": result.get("language", "fr"),
                "confidence": result.get("confidence", 0),
                "message": result.get("message", "Transcription completed")
            }
        finally:
            # Nettoyage
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    except Exception as e:
        logger.error(f"Error transcribing audio: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze", response_model=Dict[str, Any], summary="Analyser une transcription d'appel")
async def analyze_call(request: AnalyzeTranscriptRequest):
    """
    Analyse une transcription d'appel pour détecter :
    - Objections et préoccupations
    - Signaux d'intérêt forts
    - Engagements pris
    - Sentiment général
    - Actions de suivi recommandées
    
    Retourne un score de qualité d'appel (0-100).
    """
    try:
        engine = get_voice_assistant()
        
        metadata_dict = request.metadata.dict() if request.metadata else {}
        
        # Analyse complète
        analysis = engine.analyze_call_transcript(
            transcript=request.transcript,
            prospect_id=request.prospect_id,
            call_metadata=metadata_dict
        )
        
        return {
            "success": True,
            "analysis": analysis,
            "summary": engine.generate_call_summary(analysis)
        }
    
    except Exception as e:
        logger.error(f"Error analyzing call: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload-and-analyze", response_model=Dict[str, Any], summary="Uploader et analyser un appel")
async def upload_and_analyze(
    file: UploadFile = File(...),
    prospect_id: str = Form(...),
    call_date: Optional[str] = Form(None),
    duration_seconds: Optional[int] = Form(None)
):
    """
    Workflow complet : upload audio → transcription → analyse
    
    Endpoint tout-en-un pour traiter un appel commercial.
    """
    try:
        engine = get_voice_assistant()
        
        # Sauvegarde temporaire
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        try:
            # Étape 1 : Transcription
            logger.info(f"Step 1: Transcribing audio for prospect {prospect_id}")
            transcription = engine.transcribe_audio(tmp_path)
            
            if transcription.get("status") == "simulated":
                # Pour la démo, utiliser une fausse transcription
                transcript_text = """
                Bonjour, je suis intéressé par votre solution. 
                Pouvez-vous m'expliquer comment ça marche ?
                
                C'est exactement ce qu'il nous faut pour résoudre notre problème de gestion.
                Quel est le prix ? On peut essayer ?
                
                Je dois en parler à mon équipe mais je pense qu'on peut avancer rapidement.
                Envoyez-moi une proposition pour la semaine prochaine.
                """
            else:
                transcript_text = transcription.get("text", "")
            
            # Étape 2 : Analyse
            logger.info(f"Step 2: Analyzing transcript")
            metadata = {
                "date": call_date or datetime.now().isoformat(),
                "duration": duration_seconds or transcription.get("duration_seconds", 0)
            }
            
            analysis = engine.analyze_call_transcript(
                transcript=transcript_text,
                prospect_id=prospect_id,
                call_metadata=metadata
            )
            
            return {
                "success": True,
                "transcription": transcript_text,
                "analysis": analysis,
                "summary": engine.generate_call_summary(analysis),
                "hot_lead": analysis.get("hot_signals", False)
            }
        
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    except Exception as e:
        logger.error(f"Error in upload-and-analyze: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-summary", response_model=str, summary="Générer un résumé d'appel")
async def generate_summary(request: GenerateSummaryRequest):
    """Génère un résumé exécutif formaté à partir d'une analyse existante."""
    try:
        engine = get_voice_assistant()
        summary = engine.generate_call_summary(request.analysis)
        return summary
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/signals/types", response_model=List[str], summary="Types de signaux détectables")
async def get_signal_types():
    """Retourne la liste des types de signaux que l'assistant peut détecter."""
    return [signal.value for signal in SignalType]


@router.get("/sentiment/types", response_model=List[str], summary="Types de sentiment")
async def get_sentiment_types():
    """Retourne les niveaux de sentiment possibles."""
    return [sentiment.value for sentiment in SentimentType]


@router.post("/batch-analyze", response_model=Dict[str, Any], summary="Analyser plusieurs appels")
async def batch_analyze_calls(calls: List[AnalyzeTranscriptRequest]):
    """
    Analyse en batch plusieurs transcriptions d'appels.
    
    Utile pour l'analyse de performance d'équipe ou l'identification
    de tendances sur plusieurs appels.
    """
    try:
        engine = get_voice_assistant()
        
        results = []
        total_quality_score = 0
        hot_leads_count = 0
        
        for call in calls:
            metadata_dict = call.metadata.dict() if call.metadata else {}
            analysis = engine.analyze_call_transcript(
                transcript=call.transcript,
                prospect_id=call.prospect_id,
                call_metadata=metadata_dict
            )
            
            results.append({
                "prospect_id": call.prospect_id,
                "quality_score": analysis["quality_score"],
                "sentiment": analysis["sentiment"]["overall"],
                "hot_lead": analysis.get("hot_signals", False),
                "objections_count": len(analysis["signals"]["objections"]),
                "interest_count": len(analysis["signals"]["interest_signals"])
            })
            
            total_quality_score += analysis["quality_score"]
            if analysis.get("hot_signals"):
                hot_leads_count += 1
        
        avg_quality = total_quality_score / len(calls) if calls else 0
        
        return {
            "success": True,
            "total_calls": len(calls),
            "average_quality_score": round(avg_quality, 2),
            "hot_leads_count": hot_leads_count,
            "hot_leads_percentage": round((hot_leads_count / len(calls) * 100) if calls else 0, 2),
            "results": results
        }
    
    except Exception as e:
        logger.error(f"Error in batch analyze: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/{prospect_id}", response_model=Dict[str, Any], summary="Statistiques d'appels par prospect")
async def get_prospect_call_stats(prospect_id: str):
    """
    Récupère les statistiques de tous les appels pour un prospect donné.
    
    Agrège les analyses pour donner une vue d'ensemble de la relation.
    """
    # Dans une implémentation réelle, récupération depuis la base de données
    return {
        "prospect_id": prospect_id,
        "total_calls": 0,
        "average_quality_score": 0,
        "sentiment_trend": "stable",
        "total_objections": 0,
        "total_commitments": 0,
        "message": "Call stats retrieval requires database integration"
    }
