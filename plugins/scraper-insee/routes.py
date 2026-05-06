"""
Routes API pour le plugin Scraper INSEE
Recherche et création de prospects via les données INSEE
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List

# Import direct depuis le module main du plugin
import sys
from pathlib import Path
plugin_dir = Path(__file__).parent
main_path = plugin_dir / "main.py"

# Charge le module main du plugin explicitement
import importlib.util
spec = importlib.util.spec_from_file_location("scraper_insee_main", main_path)
insee_main = importlib.util.module_from_spec(spec)
spec.loader.exec_module(insee_main)

router = APIRouter(prefix="/api/v1/prospects", tags=["Prospects & INSEE"])


@router.post("")
async def api_create_prospect(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Crée un prospect à partir d'un SIRET"""
    result = await insee_main.create_prospect(request_data)
    
    if "error" in result:
        status_code = result.get("status_code", 400)
        raise HTTPException(status_code=status_code, detail=result["error"])
    
    return result


@router.get("/search")
async def api_search_prospects(q: str = Query(..., min_length=2)) -> Dict[str, Any]:
    """Recherche des entreprises par nom ou SIREN/SIRET"""
    result = await insee_main.search_prospects(q)
    
    if "error" in result:
        status_code = result.get("status_code", 400)
        raise HTTPException(status_code=status_code, detail=result["error"])
    
    return result


@router.get("/{siren}")
async def api_get_prospect_legal(siren: str) -> Dict[str, Any]:
    """Récupère les informations légales d'une entreprise par SIREN"""
    result = await insee_main.get_prospect_legal(siren)
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result
