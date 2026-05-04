"""
A/B Testing Plugin - Optimisation des campagnes d'outreach

Permet de tester scientifiquement différentes variantes de :
- Sujets d'emails
- Templates de messages
- Canaux de communication
- Horaires d'envoi
- Appels à l'action

Calcule automatiquement les taux de conversion et déclare un gagnant
selon des critères statistiques rigoureux.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import math
import logging

from loguru import logger


class TestStatus(str, Enum):
    DRAFT = "draft"
    RUNNING = "running"
    COMPLETED = "completed"
    DECLARED_WINNER = "winner_declared"


class TestType(str, Enum):
    SUBJECT_LINE = "subject_line"
    EMAIL_TEMPLATE = "email_template"
    CHANNEL = "channel"
    SEND_TIME = "send_time"
    CTA = "call_to_action"
    LANDING_PAGE = "landing_page"


class Variant:
    """Représente une variante dans un test A/B"""
    
    def __init__(self, name: str, content: Dict[str, Any], traffic_ratio: float = 0.5):
        self.name = name
        self.content = content  # Sujet, corps, canal, etc.
        self.traffic_ratio = traffic_ratio  # % du trafic alloué (0-1)
        
        # Métriques
        self.sent = 0
        self.delivered = 0
        self.opened = 0
        self.clicked = 0
        self.replied = 0
        self.converted = 0  # RDV pris / deal signé
        
        # Timestamps
        self.created_at = datetime.now()
        self.first_sent_at: Optional[datetime] = None
        self.last_sent_at: Optional[datetime] = None
    
    @property
    def open_rate(self) -> float:
        return (self.opened / self.delivered * 100) if self.delivered > 0 else 0
    
    @property
    def reply_rate(self) -> float:
        return (self.replied / self.sent * 100) if self.sent > 0 else 0
    
    @property
    def click_rate(self) -> float:
        return (self.clicked / self.delivered * 100) if self.delivered > 0 else 0
    
    @property
    def conversion_rate(self) -> float:
        return (self.converted / self.sent * 100) if self.sent > 0 else 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "content": self.content,
            "traffic_ratio": self.traffic_ratio,
            "metrics": {
                "sent": self.sent,
                "delivered": self.delivered,
                "opened": self.opened,
                "clicked": self.clicked,
                "replied": self.replied,
                "converted": self.converted,
                "open_rate_percent": round(self.open_rate, 2),
                "reply_rate_percent": round(self.reply_rate, 2),
                "click_rate_percent": round(self.click_rate, 2),
                "conversion_rate_percent": round(self.conversion_rate, 2)
            },
            "first_sent_at": self.first_sent_at.isoformat() if self.first_sent_at else None,
            "last_sent_at": self.last_sent_at.isoformat() if self.last_sent_at else None
        }


class ABTest:
    """Représente un test A/B complet"""
    
    def __init__(
        self,
        test_id: str,
        name: str,
        test_type: TestType,
        primary_metric: str = "reply_rate"
    ):
        self.test_id = test_id
        self.name = name
        self.test_type = test_type
        self.primary_metric = primary_metric
        
        self.status = TestStatus.DRAFT
        self.variants: List[Variant] = []
        
        # Configuration
        self.min_sample_size = 30  # Minimum par variante
        self.significance_level = 0.05  # 95% confiance
        self.winner_threshold = 0.10  # 10% amélioration min
        
        # Résultats
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.winner: Optional[str] = None
        self.confidence: float = 0.0
        
        self.created_at = datetime.now()
    
    def add_variant(self, name: str, content: Dict[str, Any], traffic_ratio: float = 0.5):
        """Ajoute une variante au test"""
        variant = Variant(name, content, traffic_ratio)
        self.variants.append(variant)
        logger.info(f"Variant '{name}' added to test {self.test_id}")
    
    def start(self):
        """Démarre le test"""
        if len(self.variants) < 2:
            raise ValueError("Au moins 2 variantes sont requises pour un test A/B")
        
        # Normaliser les traffic ratios
        total_ratio = sum(v.traffic_ratio for v in self.variants)
        for variant in self.variants:
            variant.traffic_ratio = variant.traffic_ratio / total_ratio
        
        self.status = TestStatus.RUNNING
        self.started_at = datetime.now()
        logger.info(f"Test A/B '{self.name}' started with {len(self.variants)} variants")
    
    def record_event(
        self,
        variant_name: str,
        event_type: str,
        prospect_id: str
    ):
        """Enregistre un événement pour une variante"""
        variant = next((v for v in self.variants if v.name == variant_name), None)
        if not variant:
            logger.warning(f"Variant '{variant_name}' not found in test {self.test_id}")
            return
        
        if event_type == "sent":
            variant.sent += 1
            if not variant.first_sent_at:
                variant.first_sent_at = datetime.now()
            variant.last_sent_at = datetime.now()
        elif event_type == "delivered":
            variant.delivered += 1
        elif event_type == "opened":
            variant.opened += 1
        elif event_type == "clicked":
            variant.clicked += 1
        elif event_type == "replied":
            variant.replied += 1
        elif event_type == "converted":
            variant.converted += 1
        
        # Vérifier si le test peut être terminé
        self._check_completion()
    
    def _check_completion(self):
        """Vérifie si le test a atteint la taille d'échantillon minimale"""
        min_samples = all(v.sent >= self.min_sample_size for v in self.variants)
        
        if min_samples and self.status == TestStatus.RUNNING:
            # Calculer la significativité statistique
            self._calculate_significance()
            
            if self.auto_declare_winner():
                self._declare_winner()
    
    def _calculate_significance(self):
        """Calcule la significativité statistique entre les variantes"""
        if len(self.variants) < 2:
            return
        
        # Comparer la variante A vs B avec un test Z
        variant_a = self.variants[0]
        variant_b = self.variants[1]
        
        # Utiliser le primary metric
        p1 = getattr(variant_a, self.primary_metric.replace("_rate", "_rate")) / 100
        p2 = getattr(variant_b, self.primary_metric.replace("_rate", "_rate")) / 100
        n1 = variant_a.sent
        n2 = variant_b.sent
        
        if n1 == 0 or n2 == 0:
            self.confidence = 0
            return
        
        # Test Z pour deux proportions
        p_pooled = (p1 * n1 + p2 * n2) / (n1 + n2)
        
        if p_pooled == 0 or p_pooled == 1:
            self.confidence = 0
            return
        
        se = math.sqrt(p_pooled * (1 - p_pooled) * (1/n1 + 1/n2))
        
        if se == 0:
            self.confidence = 0
            return
        
        z_score = abs(p1 - p2) / se
        
        # Convertir z-score en p-value (approximation)
        # Pour z=1.96, p=0.05 (95% confiance)
        # Pour z=2.58, p=0.01 (99% confiance)
        self.confidence = self._z_to_confidence(z_score)
    
    def _z_to_confidence(self, z: float) -> float:
        """Convertit un z-score en niveau de confiance"""
        # Approximation de la fonction de répartition normale
        if z < 0:
            z = abs(z)
        
        # Formule simplifiée
        confidence = 1 - (0.5 * math.exp(-0.717 * z - 0.416 * z * z))
        return min(confidence, 0.999)  # Max 99.9%
    
    def auto_declare_winner(self) -> bool:
        """Détermine automatiquement s'il faut déclarer un gagnant"""
        if not self.confidence >= (1 - self.significance_level):
            return False
        
        # Vérifier que l'amélioration dépasse le threshold
        best_variant = max(self.variants, key=lambda v: getattr(v, self.primary_metric.replace("_rate", "_rate")))
        second_best = sorted(self.variants, key=lambda v: getattr(v, self.primary_metric.replace("_rate", "_rate")), reverse=True)[1]
        
        metric_best = getattr(best_variant, self.primary_metric.replace("_rate", "_rate"))
        metric_second = getattr(second_best, self.primary_metric.replace("_rate", "_rate"))
        
        if metric_second == 0:
            return True
        
        improvement = (metric_best - metric_second) / metric_second
        return improvement >= self.winner_threshold
    
    def _declare_winner(self):
        """Déclare la variante gagnante"""
        best_variant = max(self.variants, key=lambda v: getattr(v, self.primary_metric.replace("_rate", "_rate")))
        
        self.winner = best_variant.name
        self.status = TestStatus.DECLARED_WINNER
        self.completed_at = datetime.now()
        
        logger.info(f"Winner declared for test {self.test_id}: '{best_variant.name}' "
                   f"with {best_variant.reply_rate:.2f}% reply rate ({self.confidence*100:.1f}% confidence)")
    
    def get_results(self) -> Dict[str, Any]:
        """Retourne les résultats complets du test"""
        return {
            "test_id": self.test_id,
            "name": self.name,
            "type": self.test_type.value,
            "status": self.status.value,
            "primary_metric": self.primary_metric,
            "variants": [v.to_dict() for v in self.variants],
            "winner": self.winner,
            "confidence_percent": round(self.confidence * 100, 2),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "sample_size_total": sum(v.sent for v in self.variants),
            "recommendation": self._generate_recommendation()
        }
    
    def _generate_recommendation(self) -> str:
        """Génère une recommandation basée sur les résultats"""
        if self.status != TestStatus.DECLARED_WINNER:
            if self.status == TestStatus.RUNNING:
                return "Test en cours - continuer à collecter des données"
            return "Test non terminé - aucune recommandation"
        
        winner = next((v for v in self.variants if v.name == self.winner), None)
        if not winner:
            return "Erreur - gagnant non trouvé"
        
        improvement = 0
        if len(self.variants) >= 2:
            others = [v for v in self.variants if v.name != self.winner]
            avg_others = sum(getattr(v, self.primary_metric.replace("_rate", "_rate")) for v in others) / len(others)
            if avg_others > 0:
                improvement = ((getattr(winner, self.primary_metric.replace("_rate", "_rate")) - avg_others) / avg_others) * 100
        
        return (f"Utiliser la variante '{self.winner}' qui améliore le {self.primary_metric} "
               f"de {improvement:.1f}% avec {self.confidence*100:.1f}% de confiance.")
    
    def to_dict(self) -> Dict[str, Any]:
        return self.get_results()


class ABTestingEngine:
    """Moteur principal d'A/B testing"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.testing_config = config.get("testing", {})
        self.metrics_config = config.get("metrics", {})
        self.tracking_config = config.get("tracking", {})
        
        self.tests: Dict[str, ABTest] = {}
        
        logger.info("A/B Testing Engine initialized")
    
    def create_test(
        self,
        name: str,
        test_type: TestType,
        variants: List[Dict[str, Any]],
        primary_metric: str = "reply_rate"
    ) -> ABTest:
        """Crée un nouveau test A/B"""
        test_id = f"ab_{name.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}"
        
        test = ABTest(test_id, name, test_type, primary_metric)
        
        # Configurer les paramètres depuis la config globale
        test.min_sample_size = self.testing_config.get("min_sample_size", 30)
        test.significance_level = self.testing_config.get("significance_level", 0.05)
        test.winner_threshold = self.testing_config.get("winner_threshold", 0.10)
        
        # Ajouter les variantes
        for i, variant_data in enumerate(variants):
            name = variant_data.get("name", f"Variant_{i+1}")
            content = variant_data.get("content", {})
            traffic_ratio = variant_data.get("traffic_ratio", 0.5)
            test.add_variant(name, content, traffic_ratio)
        
        self.tests[test_id] = test
        logger.info(f"Test A/B created: {test_id}")
        return test
    
    def get_test(self, test_id: str) -> Optional[ABTest]:
        """Récupère un test par son ID"""
        return self.tests.get(test_id)
    
    def start_test(self, test_id: str):
        """Démarre un test"""
        test = self.get_test(test_id)
        if not test:
            raise ValueError(f"Test {test_id} not found")
        test.start()
    
    def record_event(
        self,
        test_id: str,
        variant_name: str,
        event_type: str,
        prospect_id: str
    ):
        """Enregistre un événement pour un test"""
        test = self.get_test(test_id)
        if not test:
            logger.warning(f"Test {test_id} not found for event recording")
            return
        test.record_event(variant_name, event_type, prospect_id)
    
    def get_all_tests(self) -> List[Dict[str, Any]]:
        """Retourne tous les tests avec leurs résultats"""
        return [test.to_dict() for test in self.tests.values()]
    
    def get_running_tests(self) -> List[Dict[str, Any]]:
        """Retourne les tests en cours"""
        return [
            test.to_dict() 
            for test in self.tests.values() 
            if test.status == TestStatus.RUNNING
        ]
    
    def get_winning_variant(self, test_id: str) -> Optional[Dict[str, Any]]:
        """Retourne la variante gagnante d'un test terminé"""
        test = self.get_test(test_id)
        if not test or test.status != TestStatus.DECLARED_WINNER:
            return None
        
        winner = next((v for v in test.variants if v.name == test.winner), None)
        return winner.to_dict() if winner else None
    
    def calculate_required_sample_size(
        self,
        baseline_rate: float,
        minimum_detectable_effect: float = 0.10,
        power: float = 0.80,
        significance: float = 0.05
    ) -> int:
        """
        Calcule la taille d'échantillon nécessaire pour détecter un effet
        
        Args:
            baseline_rate: Taux de conversion actuel (ex: 0.05 pour 5%)
            minimum_detectable_effect: Effet minimum à détecter (ex: 0.10 pour 10%)
            power: Puissance statistique souhaitée (défaut: 0.80)
            significance: Niveau de significativité (défaut: 0.05)
        
        Returns:
            Taille d'échantillon requise par variante
        """
        # Formule simplifiée pour le calcul de sample size
        z_alpha = 1.96  # Pour 95% confiance
        z_beta = 0.84   # Pour 80% power
        
        p1 = baseline_rate
        p2 = baseline_rate * (1 + minimum_detectable_effect)
        
        p_pooled = (p1 + p2) / 2
        
        numerator = (z_alpha + z_beta) ** 2 * 2 * p_pooled * (1 - p_pooled)
        denominator = (p1 - p2) ** 2
        
        if denominator == 0:
            return 1000  # Valeur par défaut si pas de différence
        
        return math.ceil(numerator / denominator)


# Instance singleton
_ab_engine: Optional[ABTestingEngine] = None


def get_ab_engine(config: Optional[Dict[str, Any]] = None) -> ABTestingEngine:
    """Retourne l'instance singleton du moteur A/B testing"""
    global _ab_engine
    
    if _ab_engine is None:
        if config is None:
            raise ValueError("Config required for first initialization")
        _ab_engine = ABTestingEngine(config)
    
    return _ab_engine
