"""
Routes API pour le plugin Compliance Guard
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

router = APIRouter(prefix="/api/v1/compliance", tags=["Compliance & RGPD"])

class ComplianceCheckRequest(BaseModel):
    siret: str
    raison_sociale: str
    capital_social: Optional[float] = None
    effectifs: Optional[int] = None
    date_creation: Optional[str] = None
    ca_evolution_percent: Optional[float] = None
    procedure_collective: Optional[bool] = False

class ErasureRequest(BaseModel):
    siret: str
    reason: str = "Droit à l'oubli"

@router.post("/check")
async def check_compliance(request: ComplianceCheckRequest) -> Dict[str, Any]:
    """Vérifier la conformité RGPD et les risques pour un prospect"""
    try:
        from plugins.compliance_guard.guard import create_plugin
        guard = create_plugin()
        
        prospect_data = request.dict()
        
        result = await guard.check_compliance(prospect_data)
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/erasure/request")
async def request_erasure(request: ErasureRequest) -> Dict[str, Any]:
    """Enregistrer une demande de suppression de données (droit à l'oubli)"""
    try:
        from plugins.compliance_guard.guard import create_plugin
        guard = create_plugin()
        
        result = await guard.request_erasure(
            siret=request.siret,
            reason=request.reason
        )
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/erasure/status/{siret}")
async def get_erasure_status(siret: str) -> Dict[str, Any]:
    """Vérifier le statut d'une demande de suppression"""
    # Pour MVP: retourne un statut simulé
    return {
        "success": True,
        "data": {
            "siret": siret,
            "status": "no_request",
            "message": "Aucune demande de suppression en cours"
        }
    }

@router.get("/rgpd/audit-log")
async def get_audit_log(limit: int = 50) -> Dict[str, Any]:
    """Récupérer le journal d'audit des traitements RGPD"""
    from plugins.compliance_guard.guard import create_plugin
    guard = create_plugin()
    
    # Retourner les derniers logs
    logs = guard.processing_log[-limit:]
    
    return {
        "success": True,
        "data": {
            "count": len(logs),
            "logs": logs
        }
    }

@router.get("/fraud/indicators")
async def get_fraud_indicators() -> Dict[str, Any]:
    """Lister les indicateurs de fraude surveillés"""
    from plugins.compliance_guard.guard import FRAUD_INDICATORS
    
    return {
        "success": True,
        "data": {
            name: {
                "description": name.replace("_", " ").title(),
                "threshold": info.get("threshold", "N/A"),
                "weight": f"{info['weight'] * 100}%"
            }
            for name, info in FRAUD_INDICATORS.items()
        }
    }

@router.get("/solvency/levels")
async def get_solvency_levels() -> Dict[str, Any]:
    """Obtenir les niveaux de solvabilité et leurs critères"""
    from plugins.compliance_guard.guard import SOLVENCY_LEVELS
    
    return {
        "success": True,
        "data": {
            level: {
                "min_score": config["min"],
                "label": config["label"],
                "color": config["color"]
            }
            for level, config in SOLVENCY_LEVELS.items()
        }
    }

@router.post("/export-data/{siret}")
async def export_data(siret: str) -> Dict[str, Any]:
    """Exporter les données d'un prospect (droit d'accès RGPD)"""
    try:
        from plugins.compliance_guard.guard import create_plugin
        guard = create_plugin()
        
        result = await guard.export_personal_data(siret)
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/risk/summary")
async def get_risk_summary() -> Dict[str, Any]:
    """Résumé des risques et conformités"""
    return {
        "success": True,
        "data": {
            "risk_categories": [
                {
                    "category": "RGPD",
                    "description": "Conformité protection des données",
                    "legal_basis": "Intérêt légitime (B2B)",
                    "retention_days": 365
                },
                {
                    "category": "Fraude",
                    "description": "Détection risques financiers",
                    "sources": ["BODACC", "Infogreffe", "Pappers"],
                    "enabled": True
                },
                {
                    "category": "Solvabilité",
                    "description": "Évaluation capacité de paiement",
                    "factors": ["Ancienneté", "Effectifs", "Capital", "Évolution CA"],
                    "scale": "0-100"
                }
            ]
        }
    }

@router.get("/consent/status/{siren}")
async def get_consent_status(siren: str) -> Dict[str, Any]:
    """Vérifier le statut de consentement pour un SIREN"""
    from plugins.compliance_guard.guard import create_plugin
    guard = create_plugin()
    
    status = guard._check_consent_status(siren)
    
    return {
        "success": True,
        "data": {
            "siren": siren,
            "consent_status": status,
            "description": {
                "legitimate_interest": "Intérêt légitime - Prospection B2B autorisée",
                "opted_in": "Consentement explicite donné",
                "opted_out": "Opposition enregistrée - Ne pas contacter",
                "unknown": "Statut inconnu"
            }
        }
    }

@router.post("/consent/opt-out/{siren}")
async def register_opt_out(siren: str) -> Dict[str, Any]:
    """Enregistrer une opposition à la prospection"""
    from plugins.compliance_guard.guard import create_plugin
    guard = create_plugin()
    
    if siren not in guard.consent_registry:
        guard.consent_registry[siren] = {}
    guard.consent_registry[siren]["opt_out"] = True
    
    return {
        "success": True,
        "data": {
            "siren": siren,
            "status": "opted_out",
            "message": "Opposition enregistrée avec succès"
        }
    }
