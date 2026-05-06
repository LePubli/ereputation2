"""
Routes API pour le plugin Audit Digital
Analyse de la présence digitale, tech stack, SEO, pixels tracking
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

# Import direct depuis le module main du plugin
import sys
from pathlib import Path
plugin_dir = Path(__file__).parent
main_path = plugin_dir / "main.py"

# Charge le module main du plugin explicitement
import importlib.util
spec = importlib.util.spec_from_file_location("audit_digital_main", main_path)
audit_main = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit_main)

router = APIRouter(prefix="/api/v1/audit", tags=["Audit Digital"])


@router.post("/digital/{prospect_id}")
async def start_digital_audit(prospect_id: str) -> Dict[str, Any]:
    """Lance un audit digital pour un prospect"""
    # Utilise l'instance globale si elle existe, sinon crée une nouvelle instance
    if hasattr(audit_main, 'plugin_instance'):
        plugin = audit_main.plugin_instance
    else:
        plugin = audit_main.DigitalAuditPlugin()
    
    # Pour le MVP, retourne un statut de démarrage
    return {
        "success": True,
        "prospect_id": prospect_id,
        "status": "audit_started",
        "message": "Digital audit initiated"
    }


@router.get("/digital/{prospect_id}")
async def get_digital_audit(prospect_id: str) -> Dict[str, Any]:
    """Récupère les résultats d'un audit digital"""
    # Pour le MVP, retourne une structure vide
    return {
        "prospect_id": prospect_id,
        "audit_data": {},
        "status": "no_audit_found"
    }


@router.get("/digital/{prospect_id}/score")
async def get_digital_score(prospect_id: str) -> Dict[str, Any]:
    """Obtient le score de maturité digitale"""
    return {
        "prospect_id": prospect_id,
        "score": None,
        "message": "No audit completed yet"
    }
