"""
Voice Assistant Plugin - Transcription et analyse d'appels commerciaux

Transcrit les appels audio en texte, analyse le contenu pour détecter :
- Objections et préoccupations du prospect
- Signaux d'intérêt forts
- Engagements pris par les deux parties
- Sentiment général de l'appel
- Actions de suivi recommandées
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import json
import logging

from loguru import logger


class CallRole(str, Enum):
    SDR = "sdr"  # Sales Development Representative
    PROSPECT = "prospect"


class SentimentType(str, Enum):
    VERY_POSITIVE = "very_positive"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    VERY_NEGATIVE = "very_negative"


class SignalType(str, Enum):
    INTEREST = "interest"
    OBJECTION = "objection"
    COMMITMENT = "commitment"
    PAIN_POINT = "pain_point"
    BUDGET = "budget"
    TIMELINE = "timeline"
    DECISION_MAKER = "decision_maker"


class VoiceAssistant:
    """Moteur principal d'analyse vocale"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.stt_config = config.get("speech_to_text", {})
        self.analysis_config = config.get("analysis", {})
        self.integrations_config = config.get("integrations", {})
        
        # Patterns pour détection (en français)
        self.objection_patterns = [
            "c'est trop cher", "pas dans le budget", "on verra plus tard",
            "il faut que j'en parle", "je dois réfléchir", "rappelez-moi",
            "on a déjà un fournisseur", "pas le temps maintenant",
            "envoyez-moi une proposition", "c'est compliqué",
            "il faut convaincre la direction"
        ]
        
        self.interest_patterns = [
            "ça m'intéresse", "comment ça marche", "quel est le prix",
            "on peut essayer", "montrez-moi", "j'aimerais voir",
            "quand peut-on commencer", "c'est exactement ce qu'il nous faut",
            "parlez-moi de", "expliquez-moi", "je suis curieux",
            "ça pourrait résoudre", "bonne idée"
        ]
        
        self.commitment_patterns = [
            "je vais", "on va", "nous allons", "je m'engage",
            "je vous rappelle", "on se recontacte", "je prépare",
            "j'organise", "je planifie", "réunissez", "envoyez-moi"
        ]
        
        self.timeline_patterns = [
            "la semaine prochaine", "demain", "ce mois-ci",
            "dans 15 jours", "avant la fin du trimestre",
            "dès que possible", "rapidement", "urgent"
        ]
        
        logger.info("Voice Assistant initialized")
    
    def transcribe_audio(self, audio_file_path: str) -> Dict[str, Any]:
        """
        Transcrit un fichier audio en texte
        
        Args:
            audio_file_path: Chemin vers le fichier audio
        
        Returns:
            Transcription avec métadonnées
        """
        logger.info(f"Transcribing audio file: {audio_file_path}")
        
        # Simulation de transcription (intégration Whisper ou autre STT nécessaire)
        # Dans une implémentation réelle :
        # import whisper
        # model = whisper.load_model(self.stt_config.get("model_size", "base"))
        # result = model.transcribe(audio_file_path, language=self.stt_config.get("language", "fr"))
        
        transcription_result = {
            "status": "simulated",
            "text": "[Transcription simulée - intégrer Whisper pour la transcription réelle]",
            "duration_seconds": 0,
            "language": self.stt_config.get("language", "fr"),
            "confidence": 0.0,
            "message": "Audio transcription requires Whisper or STT API integration"
        }
        
        logger.info(f"Transcription completed (simulated)")
        return transcription_result
    
    def transcribe_audio_with_speaker_diarization(
        self, 
        audio_file_path: str
    ) -> Dict[str, Any]:
        """
        Transcrit un audio avec identification des interlocuteurs
        
        Retourne une transcription segmentée par locuteur (SDR vs Prospect)
        """
        logger.info(f"Transcribing with speaker diarization: {audio_file_path}")
        
        # Simulation
        return {
            "status": "simulated",
            "segments": [],
            "speakers_detected": 2,
            "message": "Speaker diarization requires PyAnnote or similar integration"
        }
    
    def analyze_call_transcript(
        self,
        transcript: str,
        prospect_id: str,
        call_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyse complète d'une transcription d'appel
        
        Détecte :
        - Objections
        - Signaux d'intérêt
        - Engagements
        - Points de douleur
        - Sentiment
        - Actions de suivi
        
        Args:
            transcript: Texte complet de l'appel
            prospect_id: ID du prospect
            call_metadata: Métadonnées optionnelles (durée, date, participants)
        
        Returns:
            Analyse structurée de l'appel
        """
        logger.info(f"Analyzing call transcript for prospect {prospect_id}")
        
        # Détection des signaux
        objections = self._detect_patterns(transcript, self.objection_patterns, SignalType.OBJECTION)
        interest_signals = self._detect_patterns(transcript, self.interest_patterns, SignalType.INTEREST)
        commitments = self._detect_patterns(transcript, self.commitment_patterns, SignalType.COMMITMENT)
        timeline_mentions = self._detect_patterns(transcript, self.timeline_patterns, SignalType.TIMELINE)
        
        # Analyse du sentiment
        sentiment = self._analyze_sentiment(transcript, objections, interest_signals)
        
        # Extraction des points clés
        pain_points = self._extract_pain_points(transcript)
        budget_mentions = self._extract_budget_info(transcript)
        decision_info = self._extract_decision_info(transcript)
        
        # Génération des actions de suivi
        follow_up_actions = self._generate_follow_up_actions(
            objections, commitments, timeline_mentions, sentiment
        )
        
        # Score de qualité de l'appel
        quality_score = self._calculate_call_quality_score(
            interest_signals, objections, commitments, sentiment
        )
        
        analysis_result = {
            "prospect_id": prospect_id,
            "call_date": call_metadata.get("date", datetime.now().isoformat()) if call_metadata else datetime.now().isoformat(),
            "duration_seconds": call_metadata.get("duration", 0) if call_metadata else 0,
            
            "transcript_summary": transcript[:500] + "..." if len(transcript) > 500 else transcript,
            
            "signals": {
                "objections": objections,
                "interest_signals": interest_signals,
                "commitments": commitments,
                "timeline_mentions": timeline_mentions,
                "pain_points": pain_points,
                "budget_info": budget_mentions,
                "decision_info": decision_info
            },
            
            "sentiment": {
                "overall": sentiment.value,
                "sdr_sentiment": "positive",  # À raffiner avec analyse par locuteur
                "prospect_sentiment": sentiment.value
            },
            
            "quality_score": quality_score,
            
            "follow_up_actions": follow_up_actions,
            
            "recommendations": self._generate_recommendations(
                objections, interest_signals, sentiment
            ),
            
            "hot_signals": len(interest_signals) >= 3 and len(objections) <= 2,
            
            "analyzed_at": datetime.now().isoformat()
        }
        
        logger.info(f"Call analysis completed - Quality score: {quality_score}/100")
        return analysis_result
    
    def _detect_patterns(
        self, 
        text: str, 
        patterns: List[str], 
        signal_type: SignalType
    ) -> List[Dict[str, Any]]:
        """Détecte les occurrences de patterns dans le texte"""
        detected = []
        text_lower = text.lower()
        
        for pattern in patterns:
            if pattern.lower() in text_lower:
                # Trouver le contexte (phrase complète)
                sentences = text.split('.')
                for sentence in sentences:
                    if pattern.lower() in sentence.lower():
                        detected.append({
                            "type": signal_type.value,
                            "pattern": pattern,
                            "excerpt": sentence.strip() + ".",
                            "timestamp": None  # À remplir avec timestamps si disponible
                        })
                        break
        
        return detected
    
    def _analyze_sentiment(
        self,
        transcript: str,
        objections: List[Dict[str, Any]],
        interest_signals: List[Dict[str, Any]]
    ) -> SentimentType:
        """Analyse le sentiment global de l'appel"""
        
        # Score basé sur le ratio intérêt/objections
        interest_count = len(interest_signals)
        objection_count = len(objections)
        
        if interest_count == 0 and objection_count == 0:
            return SentimentType.NEUTRAL
        
        ratio = interest_count / max(objection_count, 1)
        
        if ratio >= 3:
            return SentimentType.VERY_POSITIVE
        elif ratio >= 1.5:
            return SentimentType.POSITIVE
        elif ratio >= 0.7:
            return SentimentType.NEUTRAL
        elif ratio >= 0.3:
            return SentimentType.NEGATIVE
        else:
            return SentimentType.VERY_NEGATIVE
    
    def _extract_pain_points(self, transcript: str) -> List[Dict[str, Any]]:
        """Extrait les points de douleur mentionnés"""
        pain_keywords = [
            "problème", "difficulté", "challenge", "enjeu", "douleur",
            "frein", "blocage", "perte", "coût", "inefficace",
            "trop de temps", "manuel", "compliqué", "frustrant"
        ]
        
        return self._detect_patterns(transcript, pain_keywords, SignalType.PAIN_POINT)
    
    def _extract_budget_info(self, transcript: str) -> List[Dict[str, Any]]:
        """Extrait les mentions de budget"""
        budget_keywords = [
            "budget", "prix", "coût", "tarif", "investissement",
            "argent", "euros", "€", "k€", "mille euros"
        ]
        
        return self._detect_patterns(transcript, budget_keywords, SignalType.BUDGET)
    
    def _extract_decision_info(self, transcript: str) -> List[Dict[str, Any]]:
        """Extrait les informations sur le processus de décision"""
        decision_keywords = [
            "décision", "valider", "approuver", "direction", "management",
            "équipe", "collègues", "validé", "accord", "feu vert"
        ]
        
        return self._detect_patterns(transcript, decision_keywords, SignalType.DECISION_MAKER)
    
    def _generate_follow_up_actions(
        self,
        objections: List[Dict[str, Any]],
        commitments: List[Dict[str, Any]],
        timeline_mentions: List[Dict[str, Any]],
        sentiment: SentimentType
    ) -> List[Dict[str, Any]]:
        """Génère les actions de suivi recommandées"""
        actions = []
        
        # Actions basées sur les engagements
        for commitment in commitments:
            actions.append({
                "type": "follow_up_commitment",
                "description": f"Respecter l'engagement: {commitment['excerpt']}",
                "priority": "high",
                "source": "commitment"
            })
        
        # Actions basées sur les objections
        if objections:
            actions.append({
                "type": "address_objections",
                "description": f"Préparer des réponses aux {len(objections)} objection(s)",
                "priority": "high",
                "objections_count": len(objections)
            })
        
        # Actions basées sur le timeline
        if timeline_mentions:
            actions.append({
                "type": "schedule_follow_up",
                "description": "Planifier un suivi selon le timeline mentionné",
                "priority": "medium",
                "timeline_mentioned": True
            })
        
        # Action par défaut si pas d'actions spécifiques
        if not actions:
            actions.append({
                "type": "general_follow_up",
                "description": "Envoyer un email de suivi standard",
                "priority": "low"
            })
        
        # Ajouter une échéance basée sur le sentiment
        if sentiment in [SentimentType.VERY_POSITIVE, SentimentType.POSITIVE]:
            for action in actions:
                action["suggested_deadline"] = "48h"
        elif sentiment == SentimentType.NEGATIVE:
            for action in actions:
                action["suggested_deadline"] = "7j"
        
        return actions
    
    def _generate_recommendations(
        self,
        objections: List[Dict[str, Any]],
        interest_signals: List[Dict[str, Any]],
        sentiment: SentimentType
    ) -> List[str]:
        """Génère des recommandations stratégiques"""
        recommendations = []
        
        if len(objections) > 3:
            recommendations.append(
                "Plusieurs objections détectées : préparer un argumentaire solide "
                "et envisager un appel de découverte complémentaire."
            )
        
        if len(interest_signals) >= 3:
            recommendations.append(
                "Fort intérêt détecté : accélérer le processus et proposer "
                "une démonstration ou un essai rapidement."
            )
        
        if sentiment == SentimentType.VERY_POSITIVE:
            recommendations.append(
                "Sentiment très positif : opportunité de conclure rapidement. "
                "Préparer la proposition commerciale."
            )
        elif sentiment in [SentimentType.NEGATIVE, SentimentType.VERY_NEGATIVE]:
            recommendations.append(
                "Sentiment négatif : réévaluer l'approche ou qualifier à nouveau "
                "le besoin avant de poursuivre."
            )
        
        if not recommendations:
            recommendations.append("Poursuivre le processus de vente standard.")
        
        return recommendations
    
    def _calculate_call_quality_score(
        self,
        interest_signals: List[Dict[str, Any]],
        objections: List[Dict[str, Any]],
        commitments: List[Dict[str, Any]],
        sentiment: SentimentType
    ) -> int:
        """Calcule un score de qualité d'appel (0-100)"""
        score = 50  # Score de base
        
        # Bonus pour les signaux d'intérêt (+5 par signal, max +25)
        score += min(len(interest_signals) * 5, 25)
        
        # Malus pour les objections (-5 par objection, max -20)
        score -= min(len(objections) * 5, 20)
        
        # Bonus pour les engagements (+10 par engagement, max +20)
        score += min(len(commitments) * 10, 20)
        
        # Ajustement selon le sentiment
        sentiment_bonus = {
            SentimentType.VERY_POSITIVE: 15,
            SentimentType.POSITIVE: 10,
            SentimentType.NEUTRAL: 0,
            SentimentType.NEGATIVE: -10,
            SentimentType.VERY_NEGATIVE: -20
        }
        score += sentiment_bonus.get(sentiment, 0)
        
        # Clamp entre 0 et 100
        return max(0, min(100, score))
    
    def generate_call_summary(self, analysis: Dict[str, Any]) -> str:
        """Génère un résumé exécutif de l'appel"""
        sentiment_emoji = {
            SentimentType.VERY_POSITIVE: "🔥",
            SentimentType.POSITIVE: "✅",
            SentimentType.NEUTRAL: "😐",
            SentimentType.NEGATIVE: "⚠️",
            SentimentType.VERY_NEGATIVE: "❌"
        }
        
        sentiment = SentimentType(analysis["sentiment"]["overall"])
        
        summary_parts = [
            f"📞 Résumé d'appel - {analysis['prospect_id']}",
            f"",
            f"Sentiment: {sentiment_emoji.get(sentiment, '😐')} {sentiment.value.replace('_', ' ').title()}",
            f"Score qualité: {analysis['quality_score']}/100",
            f"",
            f"📊 Signaux détectés:",
            f"  • Intérêts: {len(analysis['signals']['interest_signals'])}",
            f"  • Objections: {len(analysis['signals']['objections'])}",
            f"  • Engagements: {len(analysis['signals']['commitments'])}",
            f"",
        ]
        
        if analysis["signals"]["objections"]:
            summary_parts.append("🚧 Principales objections:")
            for obj in analysis["signals"]["objections"][:3]:
                summary_parts.append(f"  - {obj['excerpt'][:60]}...")
            summary_parts.append("")
        
        if analysis["signals"]["interest_signals"]:
            summary_parts.append("✨ Signaux d'intérêt:")
            for sig in analysis["signals"]["interest_signals"][:3]:
                summary_parts.append(f"  - {sig['excerpt'][:60]}...")
            summary_parts.append("")
        
        if analysis["follow_up_actions"]:
            summary_parts.append("📋 Actions de suivi:")
            for action in analysis["follow_up_actions"][:3]:
                summary_parts.append(f"  [{action['priority'].upper()}] {action['description']}")
        
        return "\n".join(summary_parts)


# Instance singleton
_voice_assistant: Optional[VoiceAssistant] = None


def get_voice_assistant(config: Optional[Dict[str, Any]] = None) -> VoiceAssistant:
    """Retourne l'instance singleton du voice assistant"""
    global _voice_assistant
    
    if _voice_assistant is None:
        if config is None:
            raise ValueError("Config required for first initialization")
        _voice_assistant = VoiceAssistant(config)
    
    return _voice_assistant
