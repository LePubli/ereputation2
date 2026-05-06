"""
Plugin Pipeline Kanban - Gestion visuelle des prospects
Suivi des étapes, interactions, métriques et alertes
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from loguru import logger

from core.config import settings
from core.event_bus import event_bus


class Prospect:
    """Modèle de données pour un prospect dans le pipeline"""
    
    def __init__(
        self,
        prospect_id: str,
        siret: str = "",
        raison_sociale: str = "",
        stage: str = "nouveau",
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        last_contacted_at: Optional[datetime] = None,
        rdv_date: Optional[datetime] = None,
        estimated_value: float = 0.0,
        notes: str = ""
    ):
        self.prospect_id = prospect_id
        self.siret = siret
        self.raison_sociale = raison_sociale
        self.stage = stage
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.last_contacted_at = last_contacted_at
        self.rdv_date = rdv_date
        self.estimated_value = estimated_value
        self.notes = notes
        self.interactions: List[Dict[str, Any]] = []
        self.history: List[Dict[str, Any]] = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Sérialise le prospect en dictionnaire"""
        return {
            "prospect_id": self.prospect_id,
            "siret": self.siret,
            "raison_sociale": self.raison_sociale,
            "stage": self.stage,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_contacted_at": self.last_contacted_at.isoformat() if self.last_contacted_at else None,
            "rdv_date": self.rdv_date.isoformat() if self.rdv_date else None,
            "estimated_value": self.estimated_value,
            "notes": self.notes,
            "interactions_count": len(self.interactions),
            "history_count": len(self.history)
        }
    
    def add_interaction(self, interaction_type: str, content: str, user: str = "system") -> Dict[str, Any]:
        """Ajoute une interaction au prospect"""
        interaction = {
            "id": f"int_{len(self.interactions) + 1}",
            "type": interaction_type,  # email, call, meeting, note, whatsapp, linkedin
            "content": content,
            "user": user,
            "created_at": datetime.utcnow().isoformat()
        }
        self.interactions.append(interaction)
        self.updated_at = datetime.utcnow()
        
        if interaction_type in ["email", "call", "meeting", "whatsapp", "linkedin"]:
            self.last_contacted_at = datetime.utcnow()
        
        return interaction
    
    def change_stage(self, new_stage: str) -> Dict[str, Any]:
        """Change l'étape du prospect"""
        old_stage = self.stage
        self.stage = new_stage
        self.updated_at = datetime.utcnow()
        
        history_entry = {
            "type": "stage_change",
            "old_stage": old_stage,
            "new_stage": new_stage,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.history.append(history_entry)
        
        return history_entry


class PipelineKanbanPlugin:
    """Plugin principal pour la gestion Kanban des prospects"""
    
    STAGES = [
        {"id": "nouveau", "label": "Nouveau", "color": "blue"},
        {"id": "contacte", "label": "Contacté", "color": "yellow"},
        {"id": "rdv_pris", "label": "RDV pris", "color": "orange"},
        {"id": "negociation", "label": "En négociation", "color": "purple"},
        {"id": "gagne", "label": "Gagné", "color": "green"},
        {"id": "perdu", "label": "Perdu", "color": "red"}
    ]
    
    def __init__(self):
        self.prospects: Dict[str, Prospect] = {}
        self.alert_days_no_contact = 7
        self.alert_hours_before_rdv = 24
    
    def create_prospect(
        self,
        prospect_id: str,
        siret: str = "",
        raison_sociale: str = "",
        **kwargs
    ) -> Prospect:
        """Crée un nouveau prospect"""
        prospect = Prospect(
            prospect_id=prospect_id,
            siret=siret,
            raison_sociale=raison_sociale,
            **kwargs
        )
        self.prospects[prospect_id] = prospect
        
        logger.info(f"Created prospect {prospect_id}: {raison_sociale}")
        
        return prospect
    
    def get_prospect(self, prospect_id: str) -> Optional[Prospect]:
        """Récupère un prospect par son ID"""
        return self.prospects.get(prospect_id)
    
    def change_stage(self, prospect_id: str, new_stage: str) -> Optional[Dict[str, Any]]:
        """Change l'étape d'un prospect"""
        prospect = self.get_prospect(prospect_id)
        
        if not prospect:
            return None
        
        # Valide que le stage existe
        valid_stages = [s["id"] for s in self.STAGES]
        if new_stage not in valid_stages:
            raise ValueError(f"Stage {new_stage} n'existe pas. Valid stages: {valid_stages}")
        
        history = prospect.change_stage(new_stage)
        
        # Émet événement
        event_bus.publish("prospect.stage_changed", {
            "prospect_id": prospect_id,
            "old_stage": history["old_stage"],
            "new_stage": new_stage
        })
        
        return history
    
    def add_interaction(
        self,
        prospect_id: str,
        interaction_type: str,
        content: str,
        user: str = "system"
    ) -> Optional[Dict[str, Any]]:
        """Ajoute une interaction à un prospect"""
        prospect = self.get_prospect(prospect_id)
        
        if not prospect:
            return None
        
        interaction = prospect.add_interaction(interaction_type, content, user)
        
        # Émet événement
        event_bus.publish("prospect.interaction_added", {
            "prospect_id": prospect_id,
            "interaction_type": interaction_type,
            "interaction_id": interaction["id"]
        })
        
        return interaction
    
    def get_pipeline_view(self) -> Dict[str, Any]:
        """Retourne la vue complète du pipeline Kanban"""
        columns = []
        
        for stage in self.STAGES:
            stage_prospects = [
                p.to_dict() 
                for p in self.prospects.values() 
                if p.stage == stage["id"]
            ]
            
            columns.append({
                "stage": stage,
                "count": len(stage_prospects),
                "prospects": stage_prospects
            })
        
        return {
            "columns": columns,
            "total_prospects": len(self.prospects),
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Calcule les métriques du pipeline"""
        total = len(self.prospects)
        
        if total == 0:
            return {
                "total_prospects": 0,
                "by_stage": {},
                "conversion_rates": {},
                "avg_time_per_stage": {},
                "total_estimated_value": 0
            }
        
        # Count by stage
        by_stage = {}
        for stage in self.STAGES:
            count = sum(1 for p in self.prospects.values() if p.stage == stage["id"])
            by_stage[stage["id"]] = {
                "label": stage["label"],
                "count": count,
                "percentage": round(count / total * 100, 1)
            }
        
        # Conversion rates (simplified)
        conversion_rates = {
            "nouveau_to_contacte": 0,
            "contacte_to_rdv": 0,
            "rdv_to_negociation": 0,
            "negociation_to_gagne": 0,
            "overall_win_rate": 0
        }
        
        gagne_count = sum(1 for p in self.prospects.values() if p.stage == "gagne")
        perdu_count = sum(1 for p in self.prospects.values() if p.stage == "perdu")
        
        if gagne_count + perdu_count > 0:
            conversion_rates["overall_win_rate"] = round(
                gagne_count / (gagne_count + perdu_count) * 100, 1
            )
        
        # Total estimated value
        total_value = sum(p.estimated_value for p in self.prospects.values())
        
        metrics = {
            "total_prospects": total,
            "by_stage": by_stage,
            "conversion_rates": conversion_rates,
            "total_estimated_value": total_value,
            "gagne_count": gagne_count,
            "perdu_count": perdu_count,
            "calculated_at": datetime.utcnow().isoformat()
        }
        
        event_bus.publish("pipeline.metrics_updated", metrics)
        
        return metrics
    
    def get_alerts(self) -> List[Dict[str, Any]]:
        """Génère les alertes pour les prospects"""
        alerts = []
        now = datetime.utcnow()
        
        for prospect in self.prospects.values():
            # Alerte: pas de contact depuis X jours
            if prospect.last_contacted_at:
                days_since_contact = (now - prospect.last_contacted_at).days
                if days_since_contact >= self.alert_days_no_contact:
                    alerts.append({
                        "type": "no_contact",
                        "severity": "warning",
                        "prospect_id": prospect.prospect_id,
                        "raison_sociale": prospect.raison_sociale,
                        "message": f"Pas de contact depuis {days_since_contact} jours",
                        "days": days_since_contact
                    })
            
            # Alerte: RDV dans moins de 24h
            if prospect.rdv_date:
                hours_until_rdv = (prospect.rdv_date - now).total_seconds() / 3600
                if 0 < hours_until_rdv <= self.alert_hours_before_rdv:
                    alerts.append({
                        "type": "upcoming_rdv",
                        "severity": "info",
                        "prospect_id": prospect.prospect_id,
                        "raison_sociale": prospect.raison_sociale,
                        "message": f"RDV dans {hours_until_rdv:.1f} heures",
                        "rdv_date": prospect.rdv_date.isoformat()
                    })
        
        return sorted(alerts, key=lambda x: x.get("days", float('inf')))


# Instance globale
plugin_instance = PipelineKanbanPlugin()


def init():
    """Initialisation du plugin"""
    logger.info("Initializing pipeline-kanban plugin")
    
    # S'abonner aux événements prospect.created
    from core.event_bus import event_bus
    event_bus.subscribe("prospect.created", on_prospect_created)


def cleanup():
    """Nettoyage du plugin"""
    logger.info("Cleaning up pipeline-kanban plugin")


async def on_prospect_created(event: Dict[str, Any]) -> None:
    """Handler pour l'événement prospect.created"""
    payload = event.get("payload", {})
    siret = payload.get("siret", "")
    company_data = payload.get("company_data", {})
    
    prospect_id = siret or f"prospect_{len(plugin_instance.prospects) + 1}"
    
    plugin_instance.create_prospect(
        prospect_id=prospect_id,
        siret=siret,
        raison_sociale=company_data.get("raison_sociale", ""),
        stage="nouveau"
    )
    
    logger.info(f"Auto-created prospect from event: {prospect_id}")


# Handlers API
def get_pipeline() -> Dict[str, Any]:
    """Handler GET /api/v1/pipeline"""
    return plugin_instance.get_pipeline_view()


def change_stage(prospect_id: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handler PATCH /api/v1/pipeline/{prospect_id}/stage"""
    new_stage = request_data.get("stage")
    
    if not new_stage:
        return {"error": "stage is required", "status_code": 400}
    
    try:
        result = plugin_instance.change_stage(prospect_id, new_stage)
        
        if not result:
            return {"error": "Prospect not found", "status_code": 404}
        
        return {
            "success": True,
            "prospect_id": prospect_id,
            "new_stage": new_stage,
            "history": result
        }
        
    except ValueError as e:
        return {"error": str(e), "status_code": 400}


def get_metrics() -> Dict[str, Any]:
    """Handler GET /api/v1/pipeline/metrics"""
    return plugin_instance.get_metrics()


def add_interaction(prospect_id: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handler POST /api/v1/pipeline/{prospect_id}/interactions"""
    interaction_type = request_data.get("type")
    content = request_data.get("content")
    user = request_data.get("user", "system")
    
    if not interaction_type or not content:
        return {"error": "type and content are required", "status_code": 400}
    
    result = plugin_instance.add_interaction(
        prospect_id, 
        interaction_type, 
        content, 
        user
    )
    
    if not result:
        return {"error": "Prospect not found", "status_code": 404}
    
    return {
        "success": True,
        "prospect_id": prospect_id,
        "interaction": result
    }


def get_alerts() -> Dict[str, Any]:
    """Handler GET /api/v1/pipeline/alerts"""
    alerts = plugin_instance.get_alerts()
    
    return {
        "alerts_count": len(alerts),
        "alerts": alerts
    }
