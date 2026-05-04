"""
A/B Testing Routes - API endpoints pour l'optimisation des campagnes

Endpoints pour créer, gérer et analyser des tests A/B sur les campagnes
d'outreach (sujets, templates, canaux, horaires).
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

from loguru import logger

from .engine import (
    ABTestingEngine,
    TestType,
    TestStatus,
    get_ab_engine
)


router = APIRouter(prefix="/api/v1/ab-testing", tags=["A/B Testing"])


# === Modèles de données ===

class VariantInput(BaseModel):
    name: str = Field(..., description="Nom de la variante (ex: 'Sujet direct', 'Sujet question')")
    content: Dict[str, Any] = Field(..., description="Contenu de la variante (subject, body, etc.)")
    traffic_ratio: float = Field(default=0.5, ge=0, le=1, description="Ratio de trafic (0-1)")


class CreateTestRequest(BaseModel):
    name: str = Field(..., description="Nom du test")
    test_type: str = Field(..., description="Type: subject_line, email_template, channel, send_time, cta")
    variants: List[VariantInput]
    primary_metric: str = Field(default="reply_rate", description="Métrique principale à optimiser")


class RecordEventRequest(BaseModel):
    test_id: str
    variant_name: str
    event_type: str = Field(..., description="Type: sent, delivered, opened, clicked, replied, converted")
    prospect_id: str


# === Endpoints ===

@router.post("/tests", response_model=Dict[str, Any], summary="Créer un test A/B")
async def create_ab_test(request: CreateTestRequest):
    """
    Crée un nouveau test A/B avec plusieurs variantes.
    
    Types de tests supportés :
    - subject_line : Tester différents objets d'email
    - email_template : Tester différents templates de message
    - channel : Comparer Email vs LinkedIn vs WhatsApp
    - send_time : Optimiser l'horaire d'envoi
    - cta : Tester différents appels à l'action
    """
    try:
        engine = get_ab_engine()
        
        # Validation : au moins 2 variantes
        if len(request.variants) < 2:
            raise HTTPException(
                status_code=400, 
                detail="Un test A/B nécessite au moins 2 variantes"
            )
        
        # Conversion du test_type
        try:
            test_type = TestType(request.test_type)
        except ValueError:
            valid_types = [t.value for t in TestType]
            raise HTTPException(
                status_code=400,
                detail=f"Type invalide. Types valides : {valid_types}"
            )
        
        # Création du test
        variants_data = [v.dict() for v in request.variants]
        test = engine.create_test(
            name=request.name,
            test_type=test_type,
            variants=variants_data,
            primary_metric=request.primary_metric
        )
        
        return {
            "success": True,
            "test": test.to_dict(),
            "message": f"Test A/B '{request.name}' créé avec {len(test.variants)} variantes"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating A/B test: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tests", response_model=List[Dict[str, Any]], summary="Lister tous les tests")
async def list_all_tests(status: Optional[str] = None):
    """
    Liste tous les tests A/B avec leurs résultats.
    
    Filtre optionnel par statut : draft, running, completed, winner_declared
    """
    try:
        engine = get_ab_engine()
        
        all_tests = engine.get_all_tests()
        
        if status:
            all_tests = [t for t in all_tests if t.get("status") == status]
        
        return {
            "success": True,
            "count": len(all_tests),
            "tests": all_tests
        }
    
    except Exception as e:
        logger.error(f"Error listing tests: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tests/{test_id}", response_model=Dict[str, Any], summary="Récupérer un test")
async def get_test(test_id: str):
    """Récupère les détails complets d'un test A/B spécifique."""
    try:
        engine = get_ab_engine()
        test = engine.get_test(test_id)
        
        if not test:
            raise HTTPException(status_code=404, detail=f"Test {test_id} non trouvé")
        
        return {
            "success": True,
            "test": test.to_dict()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting test: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tests/{test_id}/start", summary="Démarrer un test")
async def start_test(test_id: str):
    """
    Démarre un test A/B précédemment créé.
    
    Une fois démarré, le test commence à répartir le trafic entre les variantes.
    """
    try:
        engine = get_ab_engine()
        engine.start_test(test_id)
        
        return {
            "success": True,
            "message": f"Test {test_id} démarré",
            "status": "running"
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error starting test: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/events", summary="Enregistrer un événement")
async def record_event(request: RecordEventRequest):
    """
    Enregistre un événement de conversion pour un test A/B.
    
    Événements trackés :
    - sent : Message envoyé
    - delivered : Message délivré
    - opened : Email ouvert
    - clicked : Lien cliqué
    - replied : Prospect a répondu
    - converted : RDV pris / deal signé
    """
    try:
        engine = get_ab_engine()
        
        engine.record_event(
            test_id=request.test_id,
            variant_name=request.variant_name,
            event_type=request.event_type,
            prospect_id=request.prospect_id
        )
        
        return {
            "success": True,
            "message": f"Événement '{request.event_type}' enregistré pour la variante '{request.variant_name}'"
        }
    
    except Exception as e:
        logger.error(f"Error recording event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tests/{test_id}/winner", response_model=Dict[str, Any], summary="Récupérer le gagnant")
async def get_winner(test_id: str):
    """
    Récupère la variante gagnante d'un test terminé.
    
    Le gagnant est déterminé automatiquement selon :
    - La significativité statistique (95% confiance par défaut)
    - L'amélioration minimum (10% par défaut)
    """
    try:
        engine = get_ab_engine()
        
        winner = engine.get_winning_variant(test_id)
        
        if not winner:
            test = engine.get_test(test_id)
            if not test:
                raise HTTPException(status_code=404, detail="Test non trouvé")
            
            if test.status != TestStatus.DECLARED_WINNER:
                return {
                    "success": False,
                    "message": "Aucun gagnant déclaré pour ce test",
                    "status": test.status,
                    "recommendation": "Continuer à collecter des données ou vérifier les critères de victoire"
                }
        
        return {
            "success": True,
            "winner": winner,
            "message": f"Variante gagnante : {winner['name']}"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting winner: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sample-size-calculator", response_model=Dict[str, Any], summary="Calculateur de taille d'échantillon")
async def calculate_sample_size(
    baseline_rate: float = Field(..., description="Taux de conversion actuel (ex: 0.05 pour 5%)"),
    minimum_effect: float = Field(default=0.10, description="Effet minimum à détecter (ex: 0.10 pour 10%)"),
    power: float = Field(default=0.80, description="Puissance statistique (défaut: 0.80)"),
    significance: float = Field(default=0.05, description="Niveau de significativité (défaut: 0.05)")
):
    """
    Calcule la taille d'échantillon nécessaire pour un test A/B fiable.
    
    Utile pour planifier la durée des tests en fonction du volume de prospects.
    """
    try:
        engine = get_ab_engine()
        
        required_sample = engine.calculate_required_sample_size(
            baseline_rate=baseline_rate,
            minimum_detectable_effect=minimum_effect,
            power=power,
            significance=significance
        )
        
        return {
            "success": True,
            "required_sample_per_variant": required_sample,
            "total_required": required_sample * 2,  # Pour 2 variantes
            "details": {
                "baseline_rate_percent": baseline_rate * 100,
                "minimum_detectable_effect_percent": minimum_effect * 100,
                "confidence_level_percent": (1 - significance) * 100,
                "statistical_power_percent": power * 100
            },
            "recommendation": f"Prévoyez d'envoyer au moins {required_sample * 2} messages pour obtenir des résultats fiables"
        }
    
    except Exception as e:
        logger.error(f"Error calculating sample size: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=Dict[str, Any], summary="Statistiques globales A/B testing")
async def get_ab_stats():
    """
    Retourne les statistiques globales de tous les tests A/B.
    
    Inclut :
    - Nombre de tests par statut
    - Taux de réussite moyen
    - Meilleures améliorations observées
    """
    try:
        engine = get_ab_engine()
        
        all_tests = engine.get_all_tests()
        
        stats = {
            "total_tests": len(all_tests),
            "by_status": {
                "draft": sum(1 for t in all_tests if t.get("status") == "draft"),
                "running": sum(1 for t in all_tests if t.get("status") == "running"),
                "completed": sum(1 for t in all_tests if t.get("status") == "completed"),
                "winner_declared": sum(1 for t in all_tests if t.get("status") == "winner_declared")
            },
            "total_variants_tested": sum(len(t.get("variants", [])) for t in all_tests),
            "average_confidence": 0,
            "best_improvements": []
        }
        
        # Calculer la confiance moyenne et les meilleures améliorations
        declared_tests = [t for t in all_tests if t.get("status") == "winner_declared"]
        if declared_tests:
            avg_confidence = sum(t.get("confidence_percent", 0) for t in declared_tests) / len(declared_tests)
            stats["average_confidence"] = round(avg_confidence, 2)
            
            # Top 3 des meilleures améliorations
            sorted_tests = sorted(
                declared_tests,
                key=lambda x: x.get("confidence_percent", 0),
                reverse=True
            )[:3]
            stats["best_improvements"] = [
                {
                    "test_name": t.get("name"),
                    "winner": t.get("winner"),
                    "confidence_percent": t.get("confidence_percent"),
                    "metric": t.get("primary_metric")
                }
                for t in sorted_tests
            ]
        
        return {
            "success": True,
            "stats": stats
        }
    
    except Exception as e:
        logger.error(f"Error getting A/B stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/tests/{test_id}", summary="Supprimer un test")
async def delete_test(test_id: str):
    """Supprime un test A/B (seulement si non terminé)."""
    try:
        engine = get_ab_engine()
        test = engine.get_test(test_id)
        
        if not test:
            raise HTTPException(status_code=404, detail="Test non trouvé")
        
        if test.status == TestStatus.DECLARED_WINNER or test.status == TestStatus.COMPLETED:
            raise HTTPException(
                status_code=400,
                detail="Impossible de supprimer un test terminé. Archivez-le plutôt."
            )
        
        del engine.tests[test_id]
        
        return {
            "success": True,
            "message": f"Test {test_id} supprimé"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting test: {e}")
        raise HTTPException(status_code=500, detail=str(e))
