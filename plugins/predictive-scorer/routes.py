"""
Routes API pour le plugin Predictive Scorer
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List

router = APIRouter(prefix="/api/v1/scoring", tags=["Predictive Scoring"])

class PropensityScoreRequest(BaseModel):
    prospect_id: str
    legal_data: Dict[str, Any] = {}
    audit_digital: Dict[str, Any] = {}
    semantic_analysis: Dict[str, Any] = {}
    engagement: Dict[str, Any] = {}

class BulkScoreRequest(BaseModel):
    prospects: List[PropensityScoreRequest]

@router.post("/propensity")
async def calculate_propensity_score(request: PropensityScoreRequest) -> Dict[str, Any]:
    """Calculer le score de propension à l'achat pour un prospect"""
    try:
        from plugins.predictive_scorer.scorer import create_plugin
        scorer = create_plugin()
        
        prospect_data = {
            "id": request.prospect_id,
            "legal_data": request.legal_data,
            "audit_digital": request.audit_digital,
            "semantic_analysis": request.semantic_analysis,
            "engagement": request.engagement
        }
        
        result = await scorer.calculate_propensity_score(prospect_data)
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/categories")
async def get_lead_categories() -> Dict[str, Any]:
    """Retourner les catégories de leads et leurs seuils"""
    from plugins.predictive_scorer.scorer import PredictiveScorer
    scorer = PredictiveScorer()
    
    return {
        "success": True,
        "data": {
            "thresholds": scorer.thresholds,
            "labels": {
                "HOT": "🔥 Lead chaud - Action immédiate requise",
                "WARM": "⚡ Lead tiède - À nurturing",
                "COLD": "❄️ Lead froid - À qualifier davantage"
            }
        }
    }

@router.get("/weights")
async def get_scoring_weights() -> Dict[str, Any]:
    """Retourner les poids utilisés dans le scoring"""
    from plugins.predictive_scorer.scorer import PredictiveScorer
    scorer = PredictiveScorer()
    
    return {
        "success": True,
        "data": {
            "weights": scorer.weights,
            "description": {
                "digital_maturity": "Maturité digitale de l'entreprise",
                "financial_health": "Santé financière et stabilité",
                "pain_intensity": "Intensité des douleurs identifiées",
                "engagement_signals": "Signaux d'engagement et réactivité"
            }
        }
    }

@router.post("/batch")
async def batch_score_prospects(request: BulkScoreRequest) -> Dict[str, Any]:
    """Calculer les scores pour plusieurs prospects en batch"""
    try:
        from plugins.predictive_scorer.scorer import create_plugin
        scorer = create_plugin()
        
        results = []
        for prospect_req in request.prospects:
            prospect_data = {
                "id": prospect_req.prospect_id,
                "legal_data": prospect_req.legal_data,
                "audit_digital": prospect_req.audit_digital,
                "semantic_analysis": prospect_req.semantic_analysis,
                "engagement": prospect_req.engagement
            }
            
            score_result = await scorer.calculate_propensity_score(prospect_data)
            results.append({
                "prospect_id": prospect_req.prospect_id,
                "score": score_result
            })
        
        return {
            "success": True,
            "data": {
                "count": len(results),
                "scores": results,
                "summary": {
                    "hot_leads": sum(1 for r in results if r["score"]["category"] == "HOT"),
                    "warm_leads": sum(1 for r in results if r["score"]["category"] == "WARM"),
                    "cold_leads": sum(1 for r in results if r["score"]["category"] == "COLD")
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recommendations/{category}")
async def get_recommendations_by_category(category: str) -> Dict[str, Any]:
    """Obtenir les recommandations types par catégorie de lead"""
    if category.upper() not in ["HOT", "WARM", "COLD"]:
        raise HTTPException(status_code=400, detail="Catégorie invalide (HOT, WARM, COLD)")
    
    recommendations = {
        "HOT": [
            "📞 Contacter immédiatement par téléphone",
            "💼 Préparer une offre personnalisée",
            "📅 Proposer un rendez-vous sous 48h"
        ],
        "WARM": [
            "📧 Envoyer un email de nurturing avec contenu de valeur",
            "🔍 Approfondir la découverte des besoins",
            "🤝 Engager sur LinkedIn"
        ],
        "COLD": [
            "📊 Collecter plus d'informations",
            "🎯 Segmenter pour campagne de sensibilisation",
            "⏳ Recontacter dans 30-60 jours"
        ]
    }
    
    return {
        "success": True,
        "data": {
            "category": category.upper(),
            "recommendations": recommendations[category.upper()]
        }
    }
