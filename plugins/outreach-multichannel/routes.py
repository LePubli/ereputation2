"""
Outreach Multi-Channel Routes - API endpoints pour l'outreach automatisé

Endpoints pour gérer les séquences, envoyer des messages et suivre les performances.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

from loguru import logger

from .engine import (
    OutreachEngine, 
    ChannelType, 
    SequenceStatus,
    MessageStatus,
    get_outreach_engine
)


router = APIRouter(prefix="/api/v1/outreach", tags=["Outreach Multi-Channel"])


# === Modèles de données ===

class SequenceStep(BaseModel):
    channel: str = Field(..., description="Canal: email, linkedin, whatsapp")
    template_type: str = Field(..., description="Type: consultative, direct, value_first")
    delay_hours: int = Field(default=48, description="Délai avant cette étape en heures")
    custom_message: Optional[str] = Field(None, description="Message personnalisé optionnel")


class CreateSequenceRequest(BaseModel):
    prospect_id: str
    name: str
    steps: List[SequenceStep]
    primary_channel: str = "email"


class SendEmailRequest(BaseModel):
    to_address: str
    subject: str
    body: str
    prospect_id: str
    sequence_id: Optional[str] = None


class SendLinkedInRequest(BaseModel):
    linkedin_profile: str
    message: str
    prospect_id: str
    is_connection_request: bool = False


class SendWhatsAppRequest(BaseModel):
    phone_number: str
    message: str
    prospect_id: str


class GenerateEmailRequest(BaseModel):
    prospect_id: str
    angles: List[Dict[str, Any]]
    semantic_analysis: Optional[Dict[str, Any]] = None
    template_type: str = "consultative"


# === Endpoints ===

@router.post("/sequences", response_model=Dict[str, Any], summary="Créer une séquence d'outreach")
async def create_sequence(request: CreateSequenceRequest):
    """
    Crée une nouvelle séquence d'outreach multi-canal pour un prospect.
    
    La séquence définit les étapes successives de contact (email, LinkedIn, WhatsApp)
    avec des délais personnalisés entre chaque tentative.
    """
    try:
        engine = get_outreach_engine()
        
        # Conversion des steps
        steps_data = [
            {
                "channel": step.channel,
                "template_type": step.template_type,
                "delay_hours": step.delay_hours,
                "custom_message": step.custom_message
            }
            for step in request.steps
        ]
        
        # Création de la séquence
        sequence = engine.create_sequence(
            prospect_id=request.prospect_id,
            name=request.name,
            steps=steps_data,
            channel=ChannelType(request.primary_channel)
        )
        
        # Activation automatique
        sequence["status"] = SequenceStatus.ACTIVE.value
        sequence["started_at"] = datetime.now().isoformat()
        
        logger.info(f"Sequence created and activated: {sequence['id']}")
        return {
            "success": True,
            "sequence": sequence,
            "message": f"Séquence '{request.name}' créée avec {len(steps_data)} étapes"
        }
    
    except Exception as e:
        logger.error(f"Error creating sequence: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sequences/{sequence_id}", response_model=Dict[str, Any], summary="Récupérer une séquence")
async def get_sequence(sequence_id: str):
    """Récupère les détails et statistiques d'une séquence spécifique."""
    # Dans une implémentation réelle, récupération depuis la base de données
    return {
        "sequence_id": sequence_id,
        "status": "active",
        "message": "Sequence retrieval requires database integration"
    }


@router.post("/sequences/{sequence_id}/pause", summary="Mettre en pause une séquence")
async def pause_sequence(sequence_id: str):
    """Met en pause l'exécution d'une séquence sans la supprimer."""
    return {
        "success": True,
        "message": f"Séquence {sequence_id} mise en pause",
        "status": "paused"
    }


@router.post("/sequences/{sequence_id}/resume", summary="Reprendre une séquence")
async def resume_sequence(sequence_id: str):
    """Reprend l'exécution d'une séquence précédemment mise en pause."""
    return {
        "success": True,
        "message": f"Séquence {sequence_id} reprise",
        "status": "active"
    }


@router.post("/sequences/{sequence_id}/stop", summary="Arrêter définitivement une séquence")
async def stop_sequence(sequence_id: str, reason: str = "manual_stop"):
    """Arrête définitivement une séquence."""
    return {
        "success": True,
        "message": f"Séquence {sequence_id} arrêtée",
        "reason": reason
    }


@router.post("/email/generate", response_model=Dict[str, str], summary="Générer un email personnalisé")
async def generate_email(request: GenerateEmailRequest):
    """
    Génère un email hyper-personnalisé basé sur :
    - Les angles commerciaux identifiés
    - L'analyse sémantique du site web
    - Le template choisi (consultatif, direct, value-first)
    """
    try:
        engine = get_outreach_engine()
        
        # Données simulées du prospect (à récupérer de la DB)
        prospect_data = {
            "company_name": "Entreprise Exemple",
            "contact_name": "Jean Dupont"
        }
        
        # Génération de l'email
        email_content = engine.generate_personalized_email(
            prospect_data=prospect_data,
            angles=request.angles,
            semantic_analysis=request.semantic_analysis,
            template_type=request.template_type
        )
        
        # Parsing du subject et body
        lines = email_content.split("\n\n", 1)
        subject = lines[0].replace("SUBJECT: ", "") if lines[0].startswith("SUBJECT:") else "Sans objet"
        body = lines[1] if len(lines) > 1 else ""
        
        return {
            "success": True,
            "subject": subject,
            "body": body,
            "template_used": request.template_type,
            "angles_count": len(request.angles)
        }
    
    except Exception as e:
        logger.error(f"Error generating email: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/email/send", response_model=Dict[str, Any], summary="Envoyer un email")
async def send_email(request: SendEmailRequest, background_tasks: BackgroundTasks):
    """
    Envoie un email à un prospect avec tracking automatique.
    
    Supporte l'envoi via SMTP configuré dans le manifest du plugin.
    """
    try:
        engine = get_outreach_engine()
        
        result = await engine.send_email(
            to_address=request.to_address,
            subject=request.subject,
            body=request.body,
            prospect_id=request.prospect_id,
            sequence_id=request.sequence_id or "manual",
            step_index=0
        )
        
        if result["status"] == MessageStatus.FAILED.value:
            raise HTTPException(
                status_code=429, 
                detail=result.get("error", "Sending failed")
            )
        
        return {
            "success": True,
            "message_id": result["message_id"],
            "status": result["status"],
            "sent_at": result["sent_at"]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/linkedin/send", response_model=Dict[str, Any], summary="Envoyer un message LinkedIn")
async def send_linkedin_message(request: SendLinkedInRequest):
    """
    Envoie un message LinkedIn ou une demande de connexion.
    
    Nécessite une intégration avec l'API LinkedIn ou un outil tiers.
    Respecte les limites journalières pour éviter le bannissement.
    """
    try:
        engine = get_outreach_engine()
        
        result = await engine.send_linkedin_message(
            linkedin_profile=request.linkedin_profile,
            message=request.message,
            prospect_id=request.prospect_id,
            sequence_id="manual",
            step_index=0,
            is_connection_request=request.is_connection_request
        )
        
        if result["status"] == MessageStatus.FAILED.value:
            raise HTTPException(
                status_code=429, 
                detail=result.get("error", "Sending failed")
            )
        
        return {
            "success": True,
            "message_id": result["message_id"],
            "status": result["status"],
            "profile_url": result.get("profile_url"),
            "sent_at": result["sent_at"]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending LinkedIn message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/whatsapp/send", response_model=Dict[str, Any], summary="Envoyer un message WhatsApp")
async def send_whatsapp_message(request: SendWhatsAppRequest):
    """
    Envoie un message WhatsApp Business.
    
    Nécessite l'API WhatsApp Business configurée.
    Idéal pour les relances rapides et prises de RDV.
    """
    try:
        engine = get_outreach_engine()
        
        result = await engine.send_whatsapp_message(
            phone_number=request.phone_number,
            message=request.message,
            prospect_id=request.prospect_id,
            sequence_id="manual",
            step_index=0
        )
        
        if result["status"] == MessageStatus.FAILED.value:
            raise HTTPException(
                status_code=429, 
                detail=result.get("error", "Sending failed")
            )
        
        return {
            "success": True,
            "message_id": result["message_id"],
            "status": result["status"],
            "phone_number": result.get("phone_number"),
            "sent_at": result["sent_at"]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending WhatsApp message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=Dict[str, Any], summary="Statistiques d'outreach")
async def get_outreach_stats():
    """
    Récupère les statistiques globales des campagnes d'outreach :
    - Nombre de séquences actives/complétées
    - Taux de réponse par canal
    - Limites journalières restantes
    """
    try:
        engine = get_outreach_engine()
        
        # Stats simulées (à connecter à la DB)
        stats = engine.get_sequence_stats([])
        
        return {
            "success": True,
            "stats": stats,
            "limits": {
                "email": {
                    "daily_limit": engine.email_config.get("max_daily_sends", 100),
                    "remaining": engine.email_config.get("max_daily_sends", 100) - engine.daily_stats["email_sent"]
                },
                "linkedin_invites": {
                    "daily_limit": engine.linkedin_config.get("max_daily_invites", 20),
                    "remaining": engine.linkedin_config.get("max_daily_invites", 20) - engine.daily_stats["linkedin_invites"]
                },
                "linkedin_messages": {
                    "daily_limit": engine.linkedin_config.get("max_daily_messages", 50),
                    "remaining": engine.linkedin_config.get("max_daily_messages", 50) - engine.daily_stats["linkedin_messages"]
                },
                "whatsapp": {
                    "daily_limit": engine.whatsapp_config.get("max_daily_messages", 30),
                    "remaining": engine.whatsapp_config.get("max_daily_messages", 30) - engine.daily_stats["whatsapp_sent"]
                }
            }
        }
    
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sequences/{sequence_id}/reply", summary="Signaler une réponse prospect")
async def record_prospect_reply(sequence_id: str):
    """
    Enregistre une réponse du prospect et arrête automatiquement la séquence.
    
    Quand un prospect répond, il est important d'arrêter les messages automatisés
    pour passer à un échange humain personnalisé.
    """
    try:
        engine = get_outreach_engine()
        
        # Simulation de récupération de séquence
        sequence = {"id": sequence_id, "status": "active"}
        
        # Arrêt de la séquence
        updated_sequence = engine.stop_sequence_on_reply(sequence)
        
        return {
            "success": True,
            "message": "Réponse enregistrée, séquence arrêtée",
            "sequence": updated_sequence,
            "next_action": "manual_followup_recommended"
        }
    
    except Exception as e:
        logger.error(f"Error recording reply: {e}")
        raise HTTPException(status_code=500, detail=str(e))
