"""
Plugin: Compliance Guard
Gestionnaire de conformité RGPD et vérification de fraude/solvabilité
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from loguru import logger
import hashlib
import json

# Indicateurs de risque de fraude
FRAUD_INDICATORS = {
    "capital_social_tres_faible": {"threshold": 1000, "weight": 0.3},
    "chiffre_affaires_en_baisse": {"threshold": -0.2, "weight": 0.25},
    "effectifs_en_chute_libre": {"threshold": -0.5, "weight": 0.2},
    "procedure_collective": {"weight": 0.5},
    "dirigeant_multiple_societes_radiees": {"weight": 0.4},
    "adresse_siege_suspecte": {"weight": 0.15}
}

# Niveaux de solvabilité
SOLVENCY_LEVELS = {
    "excellent": {"min": 80, "label": "Excellent", "color": "green"},
    "bon": {"min": 60, "label": "Bon", "color": "blue"},
    "moyen": {"min": 40, "label": "Moyen", "color": "orange"},
    "faible": {"min": 20, "label": "Faible", "color": "red"},
    "critique": {"min": 0, "label": "Critique", "color": "darkred"}
}


class ComplianceGuard:
    def __init__(self, event_bus=None):
        self.event_bus = event_bus
        self.config = {
            "rgpd": {
                "retention_days": 365,
                "auto_anonymize": True,
                "consent_tracking": True
            },
            "fraud_check": {
                "enabled": True,
                "sources": ["bodacc", "infogreffe", "pappers"]
            },
            "solvency": {
                "min_score": 50,
                "check_financials": True
            }
        }
        # Stockage des consentements (en prod: base de données)
        self.consent_registry = {}
        # Historique des traitements RGPD
        self.processing_log = []
    
    async def check_compliance(self, prospect_data: Dict[str, Any]) -> Dict[str, Any]:
        """Vérifie la conformité RGPD et les risques pour un prospect"""
        logger.info(f"Vérification conformité pour prospect: {prospect_data.get('siret')}")
        
        siret = prospect_data.get("siret")
        
        # Vérification RGPD
        rgpd_status = await self._check_rgpd_compliance(prospect_data)
        
        # Vérification fraude
        fraud_risk = await self._assess_fraud_risk(prospect_data)
        
        # Calcul solvabilité
        solvency_score = await self._calculate_solvency(prospect_data)
        
        result = {
            "siret": siret,
            "checked_at": datetime.utcnow().isoformat(),
            "rgpd": rgpd_status,
            "fraud_risk": fraud_risk,
            "solvency": solvency_score,
            "overall_risk": self._calculate_overall_risk(rgpd_status, fraud_risk, solvency_score),
            "recommendations": self._generate_compliance_recommendations(rgpd_status, fraud_risk, solvency_score)
        }
        
        # Logging du traitement
        self._log_processing("compliance_check", siret, result)
        
        # Émission d'événement
        if self.event_bus:
            await self.event_bus.publish("compliance.check_completed", {
                "siret": siret,
                "overall_risk": result["overall_risk"]["level"]
            })
        
        return result
    
    async def _check_rgpd_compliance(self, prospect_data: Dict) -> Dict[str, Any]:
        """Vérifie la conformité RGPD pour un prospect B2B"""
        siret = prospect_data.get("siret")
        siren = siret[:9] if siret else None
        
        # Vérifier si données B2B uniquement (pas de données personnelles sensibles)
        is_b2b_only = self._verify_b2b_data(prospect_data)
        
        # Vérifier consentement si nécessaire
        consent_status = "not_required"
        if self.config["rgpd"]["consent_tracking"]:
            consent_status = self._check_consent_status(siren)
        
        # Vérifier durée de rétention
        retention_status = self._check_retention_period(siret)
        
        # Droit à l'oubli - vérifier si demande exists
        erasure_request = self._check_erasure_request(siret)
        
        return {
            "compliant": is_b2b_only and not erasure_request,
            "data_type": "B2B" if is_b2b_only else "MIXED",
            "consent_status": consent_status,
            "retention_status": retention_status,
            "erasure_requested": erasure_request,
            "anonymization_due": retention_status["days_remaining"] < 30,
            "details": {
                "legal_basis": "Intérêt légitime (B2B prospecting)",
                "retention_days": self.config["rgpd"]["retention_days"],
                "data_categories": self._identify_data_categories(prospect_data)
            }
        }
    
    def _verify_b2b_data(self, data: Dict) -> bool:
        """Vérifie que seules des données B2B sont stockées"""
        # Données B2B acceptables
        allowed_fields = [
            "siret", "siren", "raison_sociale", "adresse", "code_naf",
            "effectifs", "chiffre_affaires", "site_web", "telephone_pro",
            "email_pro", "linkedin_company"
        ]
        
        # Vérifier absence de données personnelles sensibles
        sensitive_patterns = [
            "date_naissance", "numero_securite_sociale", "etat_civil",
            "opinion_politique", "croyance_religieuse", "sante"
        ]
        
        for key in data.keys():
            if any(pattern in key.lower() for pattern in sensitive_patterns):
                return False
        
        return True
    
    def _check_consent_status(self, siren: str) -> str:
        """Vérifie le statut de consentement pour un SIREN"""
        if not siren:
            return "unknown"
        
        if siren in self.consent_registry:
            record = self.consent_registry[siren]
            if record.get("opt_out"):
                return "opted_out"
            elif record.get("opt_in"):
                return "opted_in"
        
        # B2B prospecting: intérêt légitime, pas de consentement requis initialement
        return "legitimate_interest"
    
    def _check_retention_period(self, siret: str) -> Dict[str, Any]:
        """Vérifie la durée de rétention des données"""
        # En production: vérifier dans la base de données
        # Pour MVP: simulation
        first_seen = datetime.utcnow() - timedelta(days=180)  # Exemple: 6 mois
        days_stored = (datetime.utcnow() - first_seen).days
        days_remaining = self.config["rgpd"]["retention_days"] - days_stored
        
        return {
            "first_seen": first_seen.isoformat(),
            "days_stored": days_stored,
            "days_remaining": max(0, days_remaining),
            "deletion_date": (first_seen + timedelta(days=self.config["rgpd"]["retention_days"])).isoformat()
        }
    
    def _check_erasure_request(self, siret: str) -> bool:
        """Vérifie s'il y a une demande de suppression (droit à l'oubli)"""
        # En production: vérifier dans la base de données des demandes
        return False
    
    def _identify_data_categories(self, data: Dict) -> List[str]:
        """Identifie les catégories de données traitées"""
        categories = []
        
        if any(k in data for k in ["siret", "siren", "raison_sociale"]):
            categories.append("identification_entreprise")
        if any(k in data for k in ["adresse", "telephone_pro"]):
            categories.append("coordonnees_professionnelles")
        if any(k in data for k in ["effectifs", "chiffre_affaires"]):
            categories.append("donnees_economiques")
        if any(k in data for k in ["site_web", "linkedin_company"]):
            categories.append("presence_digitale")
        if any(k in data for k in ["email_pro"]):
            categories.append("contact_professionnel")
        
        return categories
    
    async def _assess_fraud_risk(self, prospect_data: Dict) -> Dict[str, Any]:
        """Évalue le risque de fraude"""
        if not self.config["fraud_check"]["enabled"]:
            return {"enabled": False, "risk_level": "not_checked"}
        
        risk_factors = []
        total_risk_score = 0.0
        
        # Vérification capital social
        capital = prospect_data.get("capital_social", 0)
        if capital < FRAUD_INDICATORS["capital_social_tres_faible"]["threshold"]:
            risk_factors.append({
                "factor": "capital_social_tres_faible",
                "value": capital,
                "weight": FRAUD_INDICATORS["capital_social_tres_faible"]["weight"],
                "severity": "high" if capital < 100 else "medium"
            })
            total_risk_score += FRAUD_INDICATORS["capital_social_tres_faible"]["weight"]
        
        # Vérification procédures collectives
        if prospect_data.get("procedure_collective"):
            risk_factors.append({
                "factor": "procedure_collective",
                "value": prospect_data.get("procedure_collective"),
                "weight": FRAUD_INDICATORS["procedure_collective"]["weight"],
                "severity": "critical"
            })
            total_risk_score += FRAUD_INDICATORS["procedure_collective"]["weight"]
        
        # Vérification évolution CA
        ca_evolution = prospect_data.get("ca_evolution_percent", 0)
        if ca_evolution < FRAUD_INDICATORS["chiffre_affaires_en_baisse"]["threshold"]:
            risk_factors.append({
                "factor": "chiffre_affaires_en_baisse",
                "value": ca_evolution,
                "weight": FRAUD_INDICATORS["chiffre_affaires_en_baisse"]["weight"],
                "severity": "medium"
            })
            total_risk_score += FRAUD_INDICATORS["chiffre_affaires_en_baisse"]["weight"]
        
        # Détermination niveau de risque
        risk_level = self._determine_risk_level(total_risk_score)
        
        return {
            "enabled": True,
            "risk_level": risk_level["level"],
            "risk_score": round(total_risk_score * 100, 2),
            "risk_factors": risk_factors,
            "sources_checked": self.config["fraud_check"]["sources"],
            "recommendation": risk_level["recommendation"]
        }
    
    def _determine_risk_level(self, score: float) -> Dict[str, Any]:
        """Détermine le niveau de risque basé sur le score"""
        if score >= 0.5:
            return {
                "level": "critical",
                "color": "red",
                "recommendation": "Éviter tout engagement - Risque très élevé"
            }
        elif score >= 0.3:
            return {
                "level": "high",
                "color": "orange",
                "recommendation": "Prudence extrême - Vérifications approfondies requises"
            }
        elif score >= 0.15:
            return {
                "level": "medium",
                "color": "yellow",
                "recommendation": "Vigilance recommandée - Demander garanties"
            }
        else:
            return {
                "level": "low",
                "color": "green",
                "recommendation": "Risque acceptable - Procéder normalement"
            }
    
    async def _calculate_solvency(self, prospect_data: Dict) -> Dict[str, Any]:
        """Calcule le score de solvabilité"""
        score = 50.0  # Score de base
        factors = []
        
        # Facteur: Ancienneté
        date_creation = prospect_data.get("date_creation")
        if date_creation:
            try:
                age_years = (datetime.utcnow() - datetime.fromisoformat(date_creation)).days / 365
                if age_years > 10:
                    score += 20
                    factors.append({"factor": "anciennete", "impact": "+20", "value": f"{age_years:.1f} ans"})
                elif age_years > 5:
                    score += 15
                    factors.append({"factor": "anciennete", "impact": "+15", "value": f"{age_years:.1f} ans"})
                elif age_years > 2:
                    score += 10
                    factors.append({"factor": "anciennete", "impact": "+10", "value": f"{age_years:.1f} ans"})
            except:
                pass
        
        # Facteur: Effectifs
        effectifs = prospect_data.get("effectifs", 0)
        if effectifs > 50:
            score += 15
            factors.append({"factor": "effectifs", "impact": "+15", "value": effectifs})
        elif effectifs > 10:
            score += 10
            factors.append({"factor": "effectifs", "impact": "+10", "value": effectifs})
        elif effectifs > 0:
            score += 5
            factors.append({"factor": "effectifs", "impact": "+5", "value": effectifs})
        
        # Facteur: Capital social
        capital = prospect_data.get("capital_social", 0)
        if capital > 50000:
            score += 15
            factors.append({"factor": "capital_social", "impact": "+15", "value": capital})
        elif capital > 10000:
            score += 10
            factors.append({"factor": "capital_social", "impact": "+10", "value": capital})
        elif capital > 1000:
            score += 5
            factors.append({"factor": "capital_social", "impact": "+5", "value": capital})
        
        # Facteur: Évolution CA
        ca_evolution = prospect_data.get("ca_evolution_percent", 0)
        if ca_evolution > 10:
            score += 15
            factors.append({"factor": "evolution_ca", "impact": "+15", "value": f"+{ca_evolution}%"})
        elif ca_evolution > 0:
            score += 10
            factors.append({"factor": "evolution_ca", "impact": "+10", "value": f"+{ca_evolution}%"})
        elif ca_evolution > -10:
            score += 0
            factors.append({"factor": "evolution_ca", "impact": "0", "value": f"{ca_evolution}%"})
        else:
            score -= 10
            factors.append({"factor": "evolution_ca", "impact": "-10", "value": f"{ca_evolution}%"})
        
        # Normalisation 0-100
        score = max(0, min(100, score))
        
        # Détermination niveau
        level = self._get_solvency_level(score)
        
        return {
            "score": round(score, 2),
            "level": level["level"],
            "level_label": level["label"],
            "color": level["color"],
            "factors": factors,
            "recommendation": self._get_solvency_recommendation(score)
        }
    
    def _get_solvency_level(self, score: float) -> Dict[str, Any]:
        """Retourne le niveau de solvabilité"""
        for level_name, config in sorted(SOLVENCY_LEVELS.items(), key=lambda x: x[1]["min"], reverse=True):
            if score >= config["min"]:
                return {
                    "level": level_name,
                    "label": config["label"],
                    "color": config["color"]
                }
        return SOLVENCY_LEVELS["critique"]
    
    def _get_solvency_recommendation(self, score: float) -> str:
        """Recommandation basée sur la solvabilité"""
        if score >= 80:
            return "✅ Excellente solvabilité - Conditions de paiement flexibles possibles"
        elif score >= 60:
            return "👍 Bonne solvabilité - Conditions standards recommandées"
        elif score >= 40:
            return "⚠️ Solvabilité moyenne - Paiement comptant ou acompte recommandé"
        elif score >= 20:
            return "🔴 Faible solvabilité - Paiement anticipé exigé"
        else:
            return "🚫 Solvabilité critique - Éviter tout engagement financier"
    
    def _calculate_overall_risk(self, rgpd: Dict, fraud: Dict, solvency: Dict) -> Dict[str, Any]:
        """Calcule le risque global"""
        risk_scores = []
        
        # Risque RGPD (non-conformité = risque élevé)
        if not rgpd.get("compliant", True):
            risk_scores.append(0.8)
        elif rgpd.get("erasure_requested"):
            risk_scores.append(0.9)
        else:
            risk_scores.append(0.1)
        
        # Risque fraude
        fraud_risk_map = {"critical": 0.9, "high": 0.7, "medium": 0.4, "low": 0.2, "not_checked": 0.0}
        risk_scores.append(fraud_risk_map.get(fraud.get("risk_level", "not_checked"), 0.5))
        
        # Risque solvabilité (inverse du score)
        solvency_risk = (100 - solvency.get("score", 50)) / 100
        risk_scores.append(solvency_risk)
        
        overall_score = sum(risk_scores) / len(risk_scores)
        
        if overall_score >= 0.6:
            level = "critical"
            label = "Risque Critique"
            color = "red"
        elif overall_score >= 0.4:
            level = "high"
            label = "Risque Élevé"
            color = "orange"
        elif overall_score >= 0.2:
            level = "medium"
            label = "Risque Moyen"
            color = "yellow"
        else:
            level = "low"
            label = "Risque Faible"
            color = "green"
        
        return {
            "score": round(overall_score * 100, 2),
            "level": level,
            "label": label,
            "color": color
        }
    
    def _generate_compliance_recommendations(self, rgpd: Dict, fraud: Dict, solvency: Dict) -> List[str]:
        """Génère des recommandations de conformité"""
        recommendations = []
        
        # Recommandations RGPD
        if not rgpd.get("compliant"):
            recommendations.append("❌ Mettre en conformité les données avant toute utilisation")
        if rgpd.get("anonymization_due"):
            recommendations.append("⏰ Anonymiser les données sous 30 jours")
        if rgpd.get("erasure_requested"):
            recommendations.append("🗑️ Supprimer immédiatement les données (droit à l'oubli)")
        
        # Recommandations Fraude
        if fraud.get("risk_level") == "critical":
            recommendations.append("🚫 Prospect à haut risque de fraude - À éviter")
        elif fraud.get("risk_level") == "high":
            recommendations.append("⚠️ Vérifications complémentaires requises avant engagement")
        
        # Recommandations Solvabilité
        if solvency.get("score", 50) < 40:
            recommendations.append("💰 Exiger paiement anticipé ou acompte substantiel")
        
        if not recommendations:
            recommendations.append("✅ Aucune alerte de conformité détectée")
        
        return recommendations
    
    def _log_processing(self, operation: str, siret: str, result: Dict):
        """Loggue un traitement de données pour traçabilité RGPD"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "operation": operation,
            "siret": siret,
            "result_summary": {
                "rgpd_compliant": result.get("rgpd", {}).get("compliant"),
                "fraud_risk": result.get("fraud_risk", {}).get("risk_level"),
                "solvency_score": result.get("solvency", {}).get("score")
            }
        }
        self.processing_log.append(log_entry)
    
    async def request_erasure(self, siret: str, reason: str = "Droit à l'oubli") -> Dict[str, Any]:
        """Enregistre une demande de suppression de données"""
        # En production: enregistrer dans la base de données et déclencher suppression
        logger.warning(f"Demande de suppression pour SIRET {siret}: {reason}")
        
        # Simulation: marquage dans le registry
        siren = siret[:9]
        if siren not in self.consent_registry:
            self.consent_registry[siren] = {}
        self.consent_registry[siren]["erasure_requested"] = True
        self.consent_registry[siren]["erasure_date"] = datetime.utcnow().isoformat()
        self.consent_registry[siren]["erasure_reason"] = reason
        
        self._log_processing("erasure_request", siret, {"status": "recorded"})
        
        return {
            "status": "recorded",
            "siret": siret,
            "message": "Demande de suppression enregistrée. Traitement sous 30 jours."
        }
    
    async def export_personal_data(self, siret: str) -> Dict[str, Any]:
        """Exporte toutes les données détenues pour un prospect (droit d'accès RGPD)"""
        # En production: récupérer toutes les données de la base
        return {
            "siret": siret,
            "export_date": datetime.utcnow().isoformat(),
            "data_categories": ["identification", "coordonnees", "historique_interactions"],
            "note": "Export complet disponible sur demande formelle"
        }


# Factory pour le plugin
def create_plugin(event_bus=None):
    return ComplianceGuard(event_bus)
