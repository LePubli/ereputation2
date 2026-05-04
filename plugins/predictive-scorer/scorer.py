"""
Plugin: Predictive Scorer
Scoring prédictif de propension à l'achat basé sur données multi-sources
Approche hybride: règles métier + modèles légers
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from loguru import logger

class PredictiveScorer:
    def __init__(self, event_bus=None):
        self.event_bus = event_bus
        self.weights = {
            "digital_maturity": 0.25,
            "financial_health": 0.30,
            "pain_intensity": 0.25,
            "engagement_signals": 0.20
        }
        self.thresholds = {
            "hot_lead": 75,
            "warm_lead": 50,
            "cold_lead": 0
        }
    
    async def calculate_propensity_score(self, prospect_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calcule le score de propension à l'achat pour un prospect"""
        logger.info(f"Calcul du score pour prospect: {prospect_data.get('siret', 'N/A')}")
        
        # Extraction des composants de score
        digital_score = self._calculate_digital_score(prospect_data.get("audit_digital", {}))
        financial_score = self._calculate_financial_score(prospect_data.get("legal_data", {}))
        pain_score = self._calculate_pain_score(prospect_data.get("semantic_analysis", {}))
        engagement_score = self._calculate_engagement_score(prospect_data.get("engagement", {}))
        
        # Score pondéré global
        global_score = (
            digital_score * self.weights["digital_maturity"] +
            financial_score * self.weights["financial_health"] +
            pain_score * self.weights["pain_intensity"] +
            engagement_score * self.weights["engagement_signals"]
        )
        
        # Détermination de la catégorie
        category = self._categorize_lead(global_score)
        
        # Facteurs influençant le score
        factors = self._identify_key_factors({
            "digital": digital_score,
            "financial": financial_score,
            "pain": pain_score,
            "engagement": engagement_score
        })
        
        # Recommandations d'action
        recommendations = self._generate_recommendations(category, factors)
        
        result = {
            "global_score": round(global_score, 2),
            "category": category,
            "category_label": self._get_category_label(category),
            "component_scores": {
                "digital_maturity": round(digital_score, 2),
                "financial_health": round(financial_score, 2),
                "pain_intensity": round(pain_score, 2),
                "engagement_signals": round(engagement_score, 2)
            },
            "key_factors": factors,
            "recommendations": recommendations,
            "confidence_level": self._calculate_confidence(prospect_data),
            "calculated_at": datetime.utcnow().isoformat()
        }
        
        # Émission d'événement
        if self.event_bus:
            await self.event_bus.publish("scoring.propensity_calculated", {
                "prospect_id": prospect_data.get("id"),
                "score": global_score,
                "category": category
            })
        
        return result
    
    def _calculate_digital_score(self, audit_data: Dict) -> float:
        """Score de maturité digitale (0-100)"""
        if not audit_data:
            return 50.0  # Score par défaut
        
        score = 0.0
        
        # Présence web (25 points)
        if audit_data.get("website_active"):
            score += 15
        if audit_data.get("https_enabled"):
            score += 10
        
        # Modernité tech (25 points)
        cms = audit_data.get("cms_detected", "")
        if cms and cms.lower() not in ["inconnu", "none", ""]:
            score += 15
        if audit_data.get("performance_score", 0) > 70:
            score += 10
        
        # Tracking & Analytics (25 points)
        pixels = audit_data.get("pixels_detected", [])
        score += min(len(pixels) * 8, 25)
        
        # Réseaux sociaux (25 points)
        social_links = audit_data.get("social_links", {})
        score += min(len(social_links) * 6, 25)
        
        return min(score, 100.0)
    
    def _calculate_financial_score(self, legal_data: Dict) -> float:
        """Score de santé financière (0-100)"""
        if not legal_data:
            return 50.0
        
        score = 50.0  # Base
        
        # Effectifs (0-20 points)
        effectifs = legal_data.get("effectifs", 0)
        if effectifs > 50:
            score += 20
        elif effectifs > 10:
            score += 15
        elif effectifs > 1:
            score += 10
        
        # Ancienneté (0-20 points)
        creation_date = legal_data.get("date_creation")
        if creation_date:
            try:
                age_years = (datetime.utcnow() - datetime.fromisoformat(creation_date)).days / 365
                if age_years > 10:
                    score += 20
                elif age_years > 5:
                    score += 15
                elif age_years > 2:
                    score += 10
            except:
                pass
        
        # Code NAF favorable (0-20 points)
        code_naf = legal_data.get("code_naf", "")
        favorable_sectors = ["62", "63", "70", "71", "72", "73"]  # Tech, conseil, R&D
        if any(code_naf.startswith(sector) for sector in favorable_sectors):
            score += 20
        
        return min(score, 100.0)
    
    def _calculate_pain_score(self, semantic_data: Dict) -> float:
        """Score d'intensité des douleurs (0-100)"""
        if not semantic_data:
            return 30.0
        
        score = 30.0  # Base
        
        pain_points = semantic_data.get("pain_points", [])
        if pain_points:
            # Score basé sur la sévérité des douleurs détectées
            max_severity = max(p.get("severity", 0) for p in pain_points)
            score += max_severity * 40
            
            # Bonus si douleurs multiples
            if len(pain_points) > 2:
                score += 15
        
        # Vérification des signaux d'urgence
        urgency_keywords = ["urgent", "immédiat", "rapidement", "asap"]
        text_content = str(semantic_data.get("keywords", []))
        if any(kw in text_content.lower() for kw in urgency_keywords):
            score += 15
        
        return min(score, 100.0)
    
    def _calculate_engagement_score(self, engagement_data: Dict) -> float:
        """Score des signaux d'engagement (0-100)"""
        if not engagement_data:
            return 20.0
        
        score = 20.0  # Base
        
        # Interactions précédentes (0-40 points)
        interactions = engagement_data.get("interactions_count", 0)
        score += min(interactions * 10, 40)
        
        # Réactivité (0-30 points)
        response_rate = engagement_data.get("response_rate", 0)
        score += response_rate * 0.3
        
        # Récence du dernier contact (0-30 points)
        last_contact = engagement_data.get("last_contact_days_ago", 999)
        if last_contact < 7:
            score += 30
        elif last_contact < 30:
            score += 20
        elif last_contact < 90:
            score += 10
        
        return min(score, 100.0)
    
    def _categorize_lead(self, score: float) -> str:
        """Catégorise le lead selon son score"""
        if score >= self.thresholds["hot_lead"]:
            return "HOT"
        elif score >= self.thresholds["warm_lead"]:
            return "WARM"
        else:
            return "COLD"
    
    def _get_category_label(self, category: str) -> str:
        labels = {
            "HOT": "🔥 Lead chaud - Action immédiate requise",
            "WARM": "⚡ Lead tiède - À nurturing",
            "COLD": "❄️ Lead froid - À qualifier davantage"
        }
        return labels.get(category, category)
    
    def _identify_key_factors(self, scores: Dict[str, float]) -> List[Dict[str, Any]]:
        """Identifie les facteurs clés influençant le score"""
        factors = []
        
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        for component, score in sorted_scores:
            if score > 70:
                factors.append({
                    "factor": component,
                    "impact": "positive",
                    "score": score,
                    "description": f"{component.replace('_', ' ').title()} fort ({score:.0f}/100)"
                })
            elif score < 40:
                factors.append({
                    "factor": component,
                    "impact": "negative",
                    "score": score,
                    "description": f"{component.replace('_', ' ').title()} faible ({score:.0f}/100) - Point d'amélioration"
                })
        
        return factors[:3]  # Top 3 facteurs
    
    def _generate_recommendations(self, category: str, factors: List) -> List[str]:
        """Génère des recommandations d'action basées sur le score"""
        recommendations = []
        
        if category == "HOT":
            recommendations.append("📞 Contacter immédiatement par téléphone")
            recommendations.append("💼 Préparer une offre personnalisée")
            recommendations.append("📅 Proposer un rendez-vous sous 48h")
        elif category == "WARM":
            recommendations.append("📧 Envoyer un email de nurturing avec contenu de valeur")
            recommendations.append("🔍 Approfondir la découverte des besoins")
            recommendations.append("🤝 Engager sur LinkedIn")
        else:
            recommendations.append("📊 Collecter plus d'informations")
            recommendations.append("🎯 Segmenter pour campagne de sensibilisation")
            recommendations.append("⏳ Recontacter dans 30-60 jours")
        
        # Recommandations basées sur les facteurs faibles
        weak_factors = [f for f in factors if f.get("impact") == "negative"]
        for factor in weak_factors:
            if "digital" in factor["factor"]:
                recommendations.append("💻 Leur proposer un audit digital gratuit")
            elif "pain" in factor["factor"]:
                recommendations.append("❓ Poser des questions ouvertes pour identifier les douleurs")
        
        return recommendations
    
    def _calculate_confidence(self, prospect_data: Dict) -> str:
        """Calcule le niveau de confiance du score"""
        data_completeness = 0
        total_checks = 4
        
        if prospect_data.get("audit_digital"):
            data_completeness += 1
        if prospect_data.get("legal_data"):
            data_completeness += 1
        if prospect_data.get("semantic_analysis"):
            data_completeness += 1
        if prospect_data.get("engagement"):
            data_completeness += 1
        
        ratio = data_completeness / total_checks
        
        if ratio >= 0.75:
            return "HIGH"
        elif ratio >= 0.5:
            return "MEDIUM"
        else:
            return "LOW"

# Factory pour le plugin
def create_plugin(event_bus=None):
    return PredictiveScorer(event_bus)
