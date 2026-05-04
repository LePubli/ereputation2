"""
Routes API pour le plugin Semantic Analyzer
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, List
import httpx

router = APIRouter(prefix="/api/v1/semantic", tags=["Semantic Analysis"])

class ContentAnalysisRequest(BaseModel):
    url: str
    html_content: str

class BulkAnalysisRequest(BaseModel):
    urls: List[str]

@router.post("/analyze")
async def analyze_content(request: ContentAnalysisRequest) -> Dict[str, Any]:
    """Analyser le contenu sémantique d'une page web"""
    try:
        from plugins.semantic_analyzer.analyzer import create_plugin
        analyzer = create_plugin()
        
        result = await analyzer.analyze_website_content(
            url=request.url,
            html_content=request.html_content
        )
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze/url")
async def analyze_from_url(request: dict, background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """Récupérer et analyser le contenu d'une URL"""
    url = request.get("url")
    if not url:
        raise HTTPException(status_code=400, detail="URL requise")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers={"User-Agent": "B2B-Prospector/1.0"})
            response.raise_for_status()
            html_content = response.text
        
        from plugins.semantic_analyzer.analyzer import create_plugin
        analyzer = create_plugin()
        
        result = await analyzer.analyze_website_content(url=url, html_content=html_content)
        
        return {
            "success": True,
            "data": result
        }
    except httpx.HTTPError as e:
        raise HTTPException(status_code=400, detail=f"Erreur de récupération URL: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pain-points/categories")
async def get_pain_categories() -> Dict[str, Any]:
    """Retourner les catégories de douleurs détectables"""
    from plugins.semantic_analyzer.analyzer import PAIN_PATTERNS
    return {
        "success": True,
        "data": {
            category: len(patterns) 
            for category, patterns in PAIN_PATTERNS.items()
        }
    }

@router.get("/values/list")
async def get_value_indicators() -> Dict[str, Any]:
    """Retourner la liste des indicateurs de valeurs"""
    from plugins.semantic_analyzer.analyzer import VALUE_INDICATORS
    return {
        "success": True,
        "data": VALUE_INDICATORS
    }
