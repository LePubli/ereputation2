"""
Plugin: Automation Engine
Moteur d'automatisation des séquences multi-canales (email, LinkedIn, WhatsApp)
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from loguru import logger
import json

# Templates de messages par canal et étape
MESSAGE_TEMPLATES = {
    "email": {
        "initial": {
            "subject": "{{prospect.pain_point}} - Solution pour {{company.name}}",
            "body": """Bonjour {{contact.first_name}},

J'ai remarqué que {{company.name}} rencontre des défis concernant {{prospect.pain_point}}.

Nous accompagnons des entreprises similaires à la vôtre pour {{solution.benefit}}.

{{social_proof}}

Seriez-vous disponible pour un échange de 15 minutes cette semaine ?

Cordialement,
{{sender.name}}
{{sender.company}}"""
        },
        "followup_1": {
            "subject": "Re: {{previous.subject}}",
            "body": """Bonjour {{contact.first_name}},

Je me permets de relancer mon précédent message concernant {{prospect.pain_point}}.

Avez-vous eu l'occasion d'y réfléchir ?

Bien à vous,
{{sender.name}}"""
        },
        "followup_2": {
            "subject": "Dernière tentative - {{company.name}}",
            "body": """Bonjour {{contact.first_name}},

Dernière tentative de ma part. Si le timing n'est pas bon, je comprends parfaitement.

N'hésitez pas à me recontacter lorsque {{prospect.pain_point}} deviendra une priorité.

Bonne continuation,
{{sender.name}}"""
        }
    },
    "linkedin": {
        "connection": """Bonjour {{contact.first_name}},

Votre profil sur {{company.name}} a retenu mon attention. Je serais ravi de vous ajouter à mon réseau.

Au plaisir d'échanger,
{{sender.name}}""",
        "message_after_connect": """Merci pour la connexion {{contact.first_name}} !

Je travaille avec des entreprises comme {{company.name}} sur {{solution.benefit}}.

Si le sujet vous intéresse, je serais heureux d'en discuter.""",
        "followup": """Bonjour {{contact.first_name}},

Je voulais simplement m'assurer que mon précédent message ne s'était pas perdu.

Des nouvelles de votre côté sur {{prospect.pain_point}} ?"""
    },
    "whatsapp": {
        "initial": """👋 Bonjour {{contact.first_name}}, {{sender.name}} ici.

Je vous contacte concernant {{prospect.pain_point}} chez {{company.name}}.

Court échange possible cette semaine ?""",
        "followup": """Bonjour {{contact.first_name}},

Petit rappel concernant mon message sur {{prospect.pain_point}}.

Toujours dispo pour en parler ? 🙏"""
    }
}

# Workflows de séquences types
SEQUENCE_WORKFLOWS = {
    "standard_b2b": {
        "name": "Séquence B2B Standard",
        "steps": [
            {"day": 0, "channel": "email", "template": "initial"},
            {"day": 3, "channel": "linkedin", "template": "connection"},
            {"day": 5, "channel": "email", "template": "followup_1"},
            {"day": 7, "channel": "linkedin", "template": "message_after_connect"},
            {"day": 12, "channel": "email", "template": "followup_2"},
            {"day": 20, "channel": "whatsapp", "template": "followup"}
        ]
    },
    "aggressive_hot_lead": {
        "name": "Séquence Lead Chaud",
        "steps": [
            {"day": 0, "channel": "email", "template": "initial"},
            {"day": 1, "channel": "linkedin", "template": "connection"},
            {"day": 2, "channel": "whatsapp", "template": "initial"},
            {"day": 4, "channel": "email", "template": "followup_1"},
            {"day": 6, "channel": "linkedin", "template": "followup"}
        ]
    },
    "soft_nurturing": {
        "name": "Nurturing Doux",
        "steps": [
            {"day": 0, "channel": "email", "template": "initial"},
            {"day": 7, "channel": "email", "template": "followup_1"},
            {"day": 21, "channel": "linkedin", "template": "connection"},
            {"day": 45, "channel": "email", "template": "followup_2"}
        ]
    }
}


class AutomationEngine:
    def __init__(self, event_bus=None):
        self.event_bus = event_bus
        self.config = {
            "max_sequences_per_day": 50,
            "delay_between_messages_hours": 24,
            "working_hours": {"start": 9, "end": 18},
            "timezone": "Europe/Paris"
        }
        self.active_sequences = {}
    
    async def start_sequence(self, prospect_data: Dict[str, Any], workflow_name: str = "standard_b2b") -> Dict[str, Any]:
        """Démarre une séquence d'automatisation pour un prospect"""
        logger.info(f"Démarrage séquence {workflow_name} pour prospect {prospect_data.get('id')}")
        
        if workflow_name not in SEQUENCE_WORKFLOWS:
            raise ValueError(f"Workflow inconnu: {workflow_name}")
        
        workflow = SEQUENCE_WORKFLOWS[workflow_name]
        
        # Création de la séquence
        sequence = {
            "id": f"seq_{prospect_data.get('id')}_{datetime.utcnow().timestamp()}",
            "prospect_id": prospect_data.get("id"),
            "workflow": workflow_name,
            "status": "active",
            "started_at": datetime.utcnow(),
            "steps": workflow["steps"],
            "completed_steps": [],
            "scheduled_steps": self._schedule_steps(workflow["steps"]),
            "personalization": self._extract_personalization(prospect_data)
        }
        
        self.active_sequences[sequence["id"]] = sequence
        
        # Planification du premier step immédiat
        first_step = workflow["steps"][0]
        await self._execute_step(sequence, first_step, 0)
        
        # Émission d'événement
        if self.event_bus:
            await self.event_bus.publish("automation.sequence_started", {
                "sequence_id": sequence["id"],
                "prospect_id": prospect_data.get("id"),
                "workflow": workflow_name
            })
        
        return {
            "sequence_id": sequence["id"],
            "workflow": workflow["name"],
            "total_steps": len(workflow["steps"]),
            "estimated_duration_days": max(s["day"] for s in workflow["steps"]) + 1
        }
    
    async def execute_scheduled_steps(self):
        """Exécute les steps planifiés arrivant à échéance"""
        now = datetime.utcnow()
        
        for seq_id, sequence in list(self.active_sequences.items()):
            if sequence["status"] != "active":
                continue
            
            for step_info in sequence["scheduled_steps"]:
                if step_info["executed"] or step_info["scheduled_time"] > now:
                    continue
                
                # Vérifier heures de travail
                if not self._is_working_hours(step_info["scheduled_time"]):
                    continue
                
                step = step_info["step"]
                step_index = sequence["steps"].index(step)
                
                await self._execute_step(sequence, step, step_index)
                step_info["executed"] = True
                sequence["completed_steps"].append(step_index)
    
    async def _execute_step(self, sequence: Dict, step: Dict, step_index: int):
        """Exécute un step de séquence"""
        channel = step["channel"]
        template_key = step["template"]
        
        # Personnalisation du message
        personalized_message = self._personalize_message(
            channel=channel,
            template_key=template_key,
            personalization=sequence["personalization"]
        )
        
        # Envoi via le canal approprié
        result = await self._send_message(
            channel=channel,
            recipient=sequence["personalization"]["contact"],
            message=personalized_message
        )
        
        # Mise à jour de la séquence
        sequence["completed_steps"].append({
            "step_index": step_index,
            "channel": channel,
            "sent_at": datetime.utcnow().isoformat(),
            "message_id": result.get("message_id"),
            "status": result.get("status")
        })
        
        logger.info(f"Step {step_index} exécuté pour séquence {sequence['id']}")
        
        # Vérifier si séquence terminée
        if len(sequence["completed_steps"]) >= len(sequence["steps"]):
            sequence["status"] = "completed"
            if self.event_bus:
                await self.event_bus.publish("automation.sequence_completed", {
                    "sequence_id": sequence["id"],
                    "prospect_id": sequence["prospect_id"]
                })
    
    def _schedule_steps(self, steps: List[Dict]) -> List[Dict]:
        """Planifie les steps avec leurs dates d'exécution"""
        scheduled = []
        base_date = datetime.utcnow()
        
        for step in steps:
            scheduled_time = base_date + timedelta(days=step["day"])
            # Ajuster aux heures de travail
            scheduled_time = self._adjust_to_working_hours(scheduled_time)
            
            scheduled.append({
                "step": step,
                "scheduled_time": scheduled_time,
                "executed": False
            })
        
        return scheduled
    
    def _extract_personalization(self, prospect_data: Dict) -> Dict[str, Any]:
        """Extrait les données de personnalisation du prospect"""
        return {
            "contact": {
                "first_name": prospect_data.get("contact_first_name", "Contact"),
                "last_name": prospect_data.get("contact_last_name", ""),
                "email": prospect_data.get("contact_email", ""),
                "linkedin_url": prospect_data.get("linkedin_url", "")
            },
            "company": {
                "name": prospect_data.get("company_name", "votre entreprise"),
                "website": prospect_data.get("website", "")
            },
            "prospect": {
                "pain_point": prospect_data.get("top_pain_point", "un défi important"),
                "industry": prospect_data.get("industry", "votre secteur")
            },
            "solution": {
                "benefit": prospect_data.get("solution_benefit", "améliorer vos performances"),
                "proof": prospect_data.get("social_proof", "")
            },
            "sender": {
                "name": prospect_data.get("sender_name", "Notre équipe"),
                "company": prospect_data.get("sender_company", "Notre société")
            }
        }
    
    def _personalize_message(self, channel: str, template_key: str, personalization: Dict) -> Dict[str, str]:
        """Personnalise un template de message"""
        templates = MESSAGE_TEMPLATES.get(channel, {})
        template = templates.get(template_key, {})
        
        if not template:
            return {"error": "Template non trouvé"}
        
        result = {}
        
        for field, content in template.items():
            personalized = content
            # Remplacement des placeholders
            for key, value in self._flatten_dict(personalization).items():
                placeholder = f"{{{{{key}}}}}"
                personalized = personalized.replace(placeholder, str(value))
            result[field] = personalized
        
        return result
    
    def _flatten_dict(self, d: Dict, parent_key: str = '') -> Dict:
        """Aplatit un dictionnaire nested pour le remplacement de placeholders"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}.{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key).items())
            else:
                items.append((new_key, v))
        return dict(items)
    
    async def _send_message(self, channel: str, recipient: Dict, message: Dict) -> Dict[str, Any]:
        """Envoie un message via le canal spécifié (simulation pour MVP)"""
        # Dans une implémentation réelle, intégration avec:
        # - SMTP/SendGrid pour email
        # - LinkedIn API pour LinkedIn
        # - WhatsApp Business API pour WhatsApp
        
        logger.info(f"Envoi message {channel} à {recipient.get('first_name')}: {list(message.keys())}")
        
        # Simulation de réponse
        return {
            "message_id": f"msg_{channel}_{datetime.utcnow().timestamp()}",
            "channel": channel,
            "status": "sent",
            "sent_at": datetime.utcnow().isoformat()
        }
    
    def _is_working_hours(self, dt: datetime) -> bool:
        """Vérifie si le timestamp est dans les heures de travail"""
        hour = dt.hour
        return self.config["working_hours"]["start"] <= hour < self.config["working_hours"]["end"]
    
    def _adjust_to_working_hours(self, dt: datetime) -> datetime:
        """Ajuste un timestamp aux prochaines heures de travail"""
        if dt.hour < self.config["working_hours"]["start"]:
            dt = dt.replace(hour=self.config["working_hours"]["start"], minute=0, second=0)
        elif dt.hour >= self.config["working_hours"]["end"]:
            dt = dt.replace(hour=self.config["working_hours"]["start"], minute=0, second=0)
            dt += timedelta(days=1)
        return dt
    
    async def pause_sequence(self, sequence_id: str) -> Dict[str, Any]:
        """Met en pause une séquence"""
        if sequence_id not in self.active_sequences:
            raise ValueError(f"Séquence inconnue: {sequence_id}")
        
        self.active_sequences[sequence_id]["status"] = "paused"
        
        if self.event_bus:
            await self.event_bus.publish("automation.sequence_paused", {
                "sequence_id": sequence_id
            })
        
        return {"status": "paused", "sequence_id": sequence_id}
    
    async def resume_sequence(self, sequence_id: str) -> Dict[str, Any]:
        """Reprend une séquence en pause"""
        if sequence_id not in self.active_sequences:
            raise ValueError(f"Séquence inconnue: {sequence_id}")
        
        self.active_sequences[sequence_id]["status"] = "active"
        
        # Re-planifier les steps non exécutés
        now = datetime.utcnow()
        for step_info in self.active_sequences[sequence_id]["scheduled_steps"]:
            if not step_info["executed"] and step_info["scheduled_time"] < now:
                step_info["scheduled_time"] = self._adjust_to_working_hours(now + timedelta(hours=1))
        
        if self.event_bus:
            await self.event_bus.publish("automation.sequence_resumed", {
                "sequence_id": sequence_id
            })
        
        return {"status": "resumed", "sequence_id": sequence_id}
    
    async def stop_sequence(self, sequence_id: str) -> Dict[str, Any]:
        """Arrête définitivement une séquence"""
        if sequence_id not in self.active_sequences:
            raise ValueError(f"Séquence inconnue: {sequence_id}")
        
        self.active_sequences[sequence_id]["status"] = "stopped"
        
        if self.event_bus:
            await self.event_bus.publish("automation.sequence_stopped", {
                "sequence_id": sequence_id
            })
        
        return {"status": "stopped", "sequence_id": sequence_id}
    
    def get_sequence_status(self, sequence_id: str) -> Dict[str, Any]:
        """Retourne le statut d'une séquence"""
        if sequence_id not in self.active_sequences:
            raise ValueError(f"Séquence inconnue: {sequence_id}")
        
        sequence = self.active_sequences[sequence_id]
        return {
            "sequence_id": sequence_id,
            "workflow": sequence["workflow"],
            "status": sequence["status"],
            "progress": f"{len(sequence['completed_steps'])}/{len(sequence['steps'])}",
            "started_at": sequence["started_at"].isoformat(),
            "completed_steps": sequence["completed_steps"]
        }


# Factory pour le plugin
def create_plugin(event_bus=None):
    return AutomationEngine(event_bus)
