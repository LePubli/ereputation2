"""
Routes API pour le plugin Pain Point Engine
Génération d'angles d'approche basés sur les points de douleur détectés
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
spec = importlib.util.spec_from_file_location("pain_point_engine_main", main_path)
pain_main = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pain_main)

router = APIRouter(prefix="/api/v1/angles", tags=["Pain Points & Angles"])


@router.post("/generate")
async def api_generate_angles(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Génère des angles d'approche basés sur un audit digital"""
    result = await pain_main.generate_angles(request_data)
    
    if "error" in result:
        status_code = result.get("status_code", 400)
        raise HTTPException(status_code=status_code, detail=result["error"])
    
    return result


@router.get("/{prospect_id}")
async def api_get_angles(prospect_id: str) -> Dict[str, Any]:
    """Récupère les angles générés pour un prospect"""
    result = await pain_main.get_angles(prospect_id)
    
    if "error" in result:
        status_code = result.get("status_code", 404)
        raise HTTPException(status_code=status_code, detail=result["error"])
    
    return result


@router.post("/{angle_id}/format")
async def api_format_angle(angle_id: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Formate un angle avec un ton spécifique (consultatif, direct, etc.)"""
    result = await pain_main.format_angle(angle_id, request_data)
    
    if "error" in result:
        status_code = result.get("status_code", 404)
        raise HTTPException(status_code=status_code, detail=result["error"])
    
    return result
