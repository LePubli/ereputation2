"""
Outreach Multi-Channel Plugin - Moteur de séquences automatisées

Gère les campagnes d'outreach multi-canales (Email, LinkedIn, WhatsApp)
avec personnalisation basée sur les angles commerciaux et analyse sémantique.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

from loguru import logger


class ChannelType(str, Enum):
    EMAIL = "email"
    LINKEDIN = "linkedin"
    WHATSAPP = "whatsapp"


class SequenceStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    STOPPED = "stopped"


class MessageStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    REPLIED = "replied"
    FAILED = "failed"
    BOUNCED = "bounced"


class OutreachEngine:
    """Moteur principal d'outreach multi-canal"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.email_config = config.get("email", {})
        self.linkedin_config = config.get("linkedin", {})
        self.whatsapp_config = config.get("whatsapp", {})
        self.sequences_config = config.get("sequences", {})
        
        # Compteurs journaliers
        self.daily_stats = {
            "email_sent": 0,
            "linkedin_invites": 0,
            "linkedin_messages": 0,
            "whatsapp_sent": 0,
            "last_reset": datetime.now().date()
        }
        
        logger.info("Outreach Engine initialized")
    
    def _reset_daily_counters_if_needed(self):
        """Réinitialise les compteurs chaque jour"""
        today = datetime.now().date()
        if self.daily_stats["last_reset"] < today:
            self.daily_stats = {
                "email_sent": 0,
                "linkedin_invites": 0,
                "linkedin_messages": 0,
                "whatsapp_sent": 0,
                "last_reset": today
            }
            logger.info("Daily counters reset")
    
    def _check_rate_limit(self, channel: ChannelType, action: str) -> bool:
        """Vérifie les limites de taux pour éviter le spam"""
        self._reset_daily_counters_if_needed()
        
        limits = {
            ChannelType.EMAIL: self.email_config.get("max_daily_sends", 100),
            ChannelType.LINKEDIN: (
                self.linkedin_config.get("max_daily_invites", 20) 
                if action == "invite" 
                else self.linkedin_config.get("max_daily_messages", 50)
            ),
            ChannelType.WHATSAPP: self.whatsapp_config.get("max_daily_messages", 30)
        }
        
        current_count = self.daily_stats.get(f"{channel.value}_{action}s", 0)
        limit = limits.get(channel, 100)
        
        if current_count >= limit:
            logger.warning(f"Rate limit reached for {channel.value}/{action}: {current_count}/{limit}")
            return False
        
        return True
    
    def create_sequence(
        self,
        prospect_id: str,
        name: str,
        steps: List[Dict[str, Any]],
        channel: ChannelType = ChannelType.EMAIL
    ) -> Dict[str, Any]:
        """
        Crée une séquence d'outreach personnalisée
        
        Args:
            prospect_id: ID du prospect
            name: Nom de la séquence
            steps: Liste des étapes (message, delay_hours, channel)
            channel: Canal principal
        
        Returns:
            Configuration de la séquence créée
        """
        sequence = {
            "id": f"seq_{prospect_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "prospect_id": prospect_id,
            "name": name,
            "channel": channel.value,
            "status": SequenceStatus.DRAFT.value,
            "steps": steps,
            "created_at": datetime.now().isoformat(),
            "started_at": None,
            "completed_at": None,
            "current_step": 0,
            "stats": {
                "sent": 0,
                "delivered": 0,
                "opened": 0,
                "clicked": 0,
                "replied": 0,
                "failed": 0
            }
        }
        
        logger.info(f"Sequence created: {sequence['id']} for prospect {prospect_id}")
        return sequence
    
    def generate_personalized_email(
        self,
        prospect_data: Dict[str, Any],
        angles: List[Dict[str, Any]],
        semantic_analysis: Optional[Dict[str, Any]] = None,
        template_type: str = "consultative"
    ) -> str:
        """
        Génère un email hyper-personnalisé basé sur les angles et l'analyse sémantique
        
        Args:
            prospect_data: Données du prospect
            angles: Angles commerciaux générés
            semantic_analysis: Analyse sémantique du site web
            template_type: Type de template (consultative, direct, value-first)
        
        Returns:
            Email personnalisé
        """
        # Sélection du meilleur angle
        best_angle = max(angles, key=lambda x: x.get("score", 0)) if angles else None
        
        # Extraction des informations clés
        company_name = prospect_data.get("company_name", "votre entreprise")
        contact_name = prospect_data.get("contact_name", "")
        
        # Détection des douleurs depuis l'analyse sémantique
        pain_points = []
        if semantic_analysis:
            pain_points = semantic_analysis.get("detected_pain_points", [])
        
        # Construction de l'email selon le template
        if template_type == "consultative":
            subject = f"Question sur {company_name}"
            body = self._build_consultative_email(contact_name, company_name, best_angle, pain_points)
        elif template_type == "direct":
            subject = f"Idée pour {company_name}"
            body = self._build_direct_email(contact_name, company_name, best_angle, pain_points)
        elif template_type == "value_first":
            subject = f"Ressource pour {company_name}"
            body = self._build_value_email(contact_name, company_name, best_angle, pain_points)
        else:
            subject = f"Contact concernant {company_name}"
            body = self._build_consultative_email(contact_name, company_name, best_angle, pain_points)
        
        return f"SUBJECT: {subject}\n\n{body}"
    
    def _build_consultative_email(
        self,
        contact_name: str,
        company_name: str,
        angle: Optional[Dict[str, Any]],
        pain_points: List[str]
    ) -> str:
        """Template consultatif - axé sur la découverte"""
        greeting = f"Bonjour {contact_name}," if contact_name else "Bonjour,"
        
        angle_content = ""
        if angle:
            facts = angle.get("verified_facts", [])
            fact_str = ", ".join(facts[:2]) if facts else "votre présence digitale"
            angle_content = f"""
J'ai analysé {fact_str} et j'ai remarqué que {angle.get('description', '')}.

Cela pourrait représenter un frein à votre croissance, ou au contraire une opportunité si c'est bien maîtrisé."""
        
        pain_point_content = ""
        if pain_points:
            pain_point_content = f"""
Je vois également que vous mettez l'accent sur : {', '.join(pain_points[:2])}.
C'est un sujet crucial dans votre secteur actuellement."""
        
        return f"""{greeting}

Je me permets de vous contacter car j'ai travaillé avec des entreprises similaires à {company_name} sur des enjeux comparables.
{angle_content}
{pain_point_content}

Seriez-vous ouvert à un échange de 15 minutes cette semaine pour explorer comment nous pourrions vous accompagner ?

Bien cordialement,
[Votre nom]
"""
    
    def _build_direct_email(
        self,
        contact_name: str,
        company_name: str,
        angle: Optional[Dict[str, Any]],
        pain_points: List[str]
    ) -> str:
        """Template direct - axé sur l'action"""
        greeting = f"Bonjour {contact_name}," if contact_name else "Bonjour,"
        
        angle_content = ""
        if angle:
            angle_content = f"""
Voici ce que j'ai identifié : {angle.get('description', '')}.

Impact estimé : {angle.get('impact', 'Non quantifié')}"""
        
        return f"""{greeting}

Je vais droit au but : j'ai analysé {company_name} et j'ai une recommandation concrète.
{angle_content}

Nous avons aidé des entreprises comme la vôtre à obtenir [résultat concret] en [délai].

Disponibilité pour un appel rapide demain ou après-demain ?

Cordialement,
[Votre nom]
"""
    
    def _build_value_email(
        self,
        contact_name: str,
        company_name: str,
        angle: Optional[Dict[str, Any]],
        pain_points: List[str]
    ) -> str:
        """Template value-first - offre de valeur gratuite"""
        greeting = f"Bonjour {contact_name}," if contact_name else "Bonjour,"
        
        resource_offer = """
J'ai préparé un audit gratuit de votre présence digitale qui identifie :
- 3 points d'amélioration prioritaires
- Les meilleures pratiques de votre secteur
- Un plan d'action en 30 jours"""
        
        if angle:
            resource_offer += f"\n\nJ'y ai inclus une analyse spécifique sur : {angle.get('description', '')}"
        
        return f"""{greeting}

Plutôt que de vous faire un long discours, je préfère vous offrir quelque chose de concret.
{resource_offer}

Ça vous intéresserait de le recevoir ? Pas besoin d'appel, je vous l'envoie par retour.

Bonne journée,
[Votre nom]
"""
    
    async def send_email(
        self,
        to_address: str,
        subject: str,
        body: str,
        prospect_id: str,
        sequence_id: str,
        step_index: int
    ) -> Dict[str, Any]:
        """Envoie un email avec tracking"""
        self._reset_daily_counters_if_needed()
        
        if not self._check_rate_limit(ChannelType.EMAIL, "sent"):
            return {
                "status": MessageStatus.FAILED.value,
                "error": "Daily rate limit reached",
                "retry_after": "24h"
            }
        
        # Simulation d'envoi (à remplacer par SMTP réel)
        logger.info(f"Sending email to {to_address} for prospect {prospect_id}")
        
        # Dans une implémentation réelle :
        # msg = MIMEMultipart()
        # msg['From'] = self.email_config['from_address']
        # msg['To'] = to_address
        # msg['Subject'] = subject
        # msg.attach(MIMEText(body, 'html'))
        # 
        # with smtplib.SMTP(self.email_config['smtp_host'], self.email_config['smtp_port']) as server:
        #     server.starttls()
        #     server.login(self.email_config['smtp_user'], self.email_config['smtp_password'])
        #     server.send_message(msg)
        
        self.daily_stats["email_sent"] += 1
        
        result = {
            "status": MessageStatus.SENT.value,
            "message_id": f"msg_{prospect_id}_{step_index}_{datetime.now().timestamp()}",
            "sent_at": datetime.now().isoformat(),
            "channel": ChannelType.EMAIL.value,
            "prospect_id": prospect_id,
            "sequence_id": sequence_id,
            "step_index": step_index
        }
        
        logger.info(f"Email sent successfully: {result['message_id']}")
        return result
    
    async def send_linkedin_message(
        self,
        linkedin_profile: str,
        message: str,
        prospect_id: str,
        sequence_id: str,
        step_index: int,
        is_connection_request: bool = False
    ) -> Dict[str, Any]:
        """Envoie un message LinkedIn"""
        self._reset_daily_counters_if_needed()
        
        action = "invite" if is_connection_request else "messages"
        if not self._check_rate_limit(ChannelType.LINKEDIN, action):
            return {
                "status": MessageStatus.FAILED.value,
                "error": "Daily rate limit reached",
                "retry_after": "24h"
            }
        
        logger.info(f"Sending LinkedIn {'connection request' if is_connection_request else 'message'} to {linkedin_profile}")
        
        # Simulation (intégration API LinkedIn réelle nécessaire)
        self.daily_stats[f"linkedin_{action}"] += 1
        
        return {
            "status": MessageStatus.SENT.value,
            "message_id": f"li_{prospect_id}_{step_index}_{datetime.now().timestamp()}",
            "sent_at": datetime.now().isoformat(),
            "channel": ChannelType.LINKEDIN.value,
            "prospect_id": prospect_id,
            "sequence_id": sequence_id,
            "step_index": step_index,
            "profile_url": linkedin_profile
        }
    
    async def send_whatsapp_message(
        self,
        phone_number: str,
        message: str,
        prospect_id: str,
        sequence_id: str,
        step_index: int
    ) -> Dict[str, Any]:
        """Envoie un message WhatsApp Business"""
        self._reset_daily_counters_if_needed()
        
        if not self._check_rate_limit(ChannelType.WHATSAPP, "sent"):
            return {
                "status": MessageStatus.FAILED.value,
                "error": "Daily rate limit reached",
                "retry_after": "24h"
            }
        
        logger.info(f"Sending WhatsApp to {phone_number}")
        
        # Simulation (intégration WhatsApp Business API nécessaire)
        self.daily_stats["whatsapp_sent"] += 1
        
        return {
            "status": MessageStatus.SENT.value,
            "message_id": f"wa_{prospect_id}_{step_index}_{datetime.now().timestamp()}",
            "sent_at": datetime.now().isoformat(),
            "channel": ChannelType.WHATSAPP.value,
            "prospect_id": prospect_id,
            "sequence_id": sequence_id,
            "step_index": step_index,
            "phone_number": phone_number
        }
    
    def schedule_next_step(
        self,
        sequence: Dict[str, Any],
        current_step_result: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Planifie la prochaine étape de la séquence"""
        if current_step_result.get("status") != MessageStatus.SENT.value:
            logger.warning(f"Cannot schedule next step: current step failed")
            return None
        
        steps = sequence.get("steps", [])
        current_index = sequence.get("current_step", 0)
        
        if current_index + 1 >= len(steps):
            sequence["status"] = SequenceStatus.COMPLETED.value
            sequence["completed_at"] = datetime.now().isoformat()
            logger.info(f"Sequence {sequence['id']} completed")
            return None
        
        next_step = steps[current_index + 1]
        delay_hours = next_step.get("delay_hours", self.sequences_config.get("default_delay_hours", 48))
        scheduled_time = datetime.now() + timedelta(hours=delay_hours)
        
        scheduling_info = {
            "next_step_index": current_index + 1,
            "scheduled_at": scheduled_time.isoformat(),
            "delay_hours": delay_hours,
            "channel": next_step.get("channel", sequence["channel"]),
            "message_template": next_step.get("template", "")
        }
        
        logger.info(f"Next step scheduled for {scheduling_info['scheduled_at']}")
        return scheduling_info
    
    def stop_sequence_on_reply(self, sequence: Dict[str, Any]) -> Dict[str, Any]:
        """Arrête la séquence quand le prospect répond"""
        sequence["status"] = SequenceStatus.STOPPED.value
        sequence["stopped_reason"] = "prospect_replied"
        sequence["stopped_at"] = datetime.now().isoformat()
        
        logger.info(f"Sequence {sequence['id']} stopped due to prospect reply")
        return sequence
    
    def get_sequence_stats(self, sequences: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calcule les statistiques agrégées des séquences"""
        total_sequences = len(sequences)
        active_sequences = sum(1 for s in sequences if s.get("status") == SequenceStatus.ACTIVE.value)
        completed_sequences = sum(1 for s in sequences if s.get("status") == SequenceStatus.COMPLETED.value)
        
        total_sent = sum(s.get("stats", {}).get("sent", 0) for s in sequences)
        total_replied = sum(s.get("stats", {}).get("replied", 0) for s in sequences)
        
        reply_rate = (total_replied / total_sent * 100) if total_sent > 0 else 0
        
        return {
            "total_sequences": total_sequences,
            "active_sequences": active_sequences,
            "completed_sequences": completed_sequences,
            "total_messages_sent": total_sent,
            "total_replies": total_replied,
            "reply_rate_percent": round(reply_rate, 2),
            "daily_stats": self.daily_stats
        }


# Instance singleton
_outreach_engine: Optional[OutreachEngine] = None


def get_outreach_engine(config: Optional[Dict[str, Any]] = None) -> OutreachEngine:
    """Retourne l'instance singleton du moteur d'outreach"""
    global _outreach_engine
    
    if _outreach_engine is None:
        if config is None:
            raise ValueError("Config required for first initialization")
        _outreach_engine = OutreachEngine(config)
    
    return _outreach_engine
