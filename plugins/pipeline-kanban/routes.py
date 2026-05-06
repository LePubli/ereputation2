"""
Routes API pour le plugin Pipeline Kanban
Gestion visuelle des prospects, métriques et alertes
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List

# Import direct depuis le module main du plugin
import sys
from pathlib import Path
plugin_dir = Path(__file__).parent
main_path = plugin_dir / "main.py"

# Charge le module main du plugin explicitement
import importlib.util
spec = importlib.util.spec_from_file_location("pipeline_kanban_main", main_path)
kanban_main = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kanban_main)

router = APIRouter(prefix="/api/v1/pipeline", tags=["Pipeline Kanban"])


@router.get("")
async def list_pipeline() -> Dict[str, Any]:
    """Retourne la vue complète du pipeline Kanban"""
    return kanban_main.get_pipeline()


@router.get("/metrics")
async def pipeline_metrics() -> Dict[str, Any]:
    """Retourne les métriques du pipeline"""
    return kanban_main.get_metrics()


@router.get("/alerts")
async def pipeline_alerts() -> Dict[str, Any]:
    """Retourne les alertes du pipeline"""
    return kanban_main.get_alerts()


@router.patch("/{prospect_id}/stage")
async def update_prospect_stage(prospect_id: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Change l'étape d'un prospect"""
    result = await kanban_main.change_stage(prospect_id, request_data)
    
    if "error" in result:
        status_code = result.get("status_code", 400)
        raise HTTPException(status_code=status_code, detail=result["error"])
    
    return result


@router.post("/{prospect_id}/interactions")
async def create_interaction(prospect_id: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Ajoute une interaction à un prospect"""
    result = await kanban_main.add_interaction(prospect_id, request_data)
    
    if "error" in result:
        status_code = result.get("status_code", 400)
        raise HTTPException(status_code=status_code, detail=result["error"])
    
    return result


# Routes supplémentaires pour la gestion des prospects
@router.get("/prospects")
async def list_prospects() -> Dict[str, Any]:
    """Liste tous les prospects"""
    pipeline_view = await kanban_main.get_pipeline()
    all_prospects = []
    
    for column in pipeline_view["columns"]:
        all_prospects.extend(column["prospects"])
    
    return {
        "prospects": all_prospects,
        "total": len(all_prospects)
    }


@router.get("/prospects/{prospect_id}")
async def get_prospect(prospect_id: str) -> Dict[str, Any]:
    """Récupère un prospect spécifique"""
    prospect = kanban_main.plugin_instance.get_prospect(prospect_id)
    
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")
    
    return prospect.to_dict()


@router.post("/prospects")
async def create_prospect(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Crée un nouveau prospect"""
    prospect_id = request_data.get("prospect_id") or request_data.get("siret")
    
    if not prospect_id:
        raise HTTPException(status_code=400, detail="prospect_id or siret is required")
    
    prospect = kanban_main.plugin_instance.create_prospect(
        prospect_id=prospect_id,
        siret=request_data.get("siret", ""),
        raison_sociale=request_data.get("raison_sociale", ""),
        stage=request_data.get("stage", "nouveau"),
        estimated_value=request_data.get("estimated_value", 0.0),
        notes=request_data.get("notes", "")
    )
    
    return {
        "success": True,
        "prospect": prospect.to_dict()
    }
