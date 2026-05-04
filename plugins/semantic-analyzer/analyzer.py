"""
Plugin: Semantic Analyzer
Analyse sémantique NLP du contenu web pour détecter douleurs, valeurs et opportunités
"""
import re
from typing import Dict, List, Any, Optional
from loguru import logger
import httpx
from collections import Counter

# Mots-clés de douleur courants par secteur
PAIN_PATTERNS = {
    "inefficacite": ["lent", "complexe", "difficile", "problème", "bug", "erreur", "perte de temps"],
    "cout": ["cher", "coûteux", "budget", "dépense", "économie", "réduire les coûts"],
    "conformite": ["RGPD", "conformité", "réglementation", "norme", "certification", "audit"],
    "croissance": ["croissance", "expansion", "nouveaux marchés", "scaling", "développement"],
    "digital": ["transformation digitale", "numérique", "automatisation", "IA", "cloud"],
    "rh": ["recrutement", "talent", "formation", "turnover", "équipe", "compétences"]
}

VALUE_INDICATORS = [
    "innovation", "leader", "expert", "premium", "qualité", "excellence",
    "durable", "écologique", "responsable", "agile", "sur-mesure"
]

class SemanticAnalyzer:
    def __init__(self, event_bus=None):
        self.event_bus = event_bus
        self.language = "fr"
        self.confidence_threshold = 0.75
        
    async def analyze_website_content(self, url: str, html_content: str) -> Dict[str, Any]:
        """Analyse le contenu HTML d'un site pour extraire insights sémantiques"""
        logger.info(f"Analyse sémantique du contenu: {url}")
        
        # Extraction du texte visible
        text_content = self._extract_visible_text(html_content)
        
        # Analyse des douleurs potentielles
        pains = self._detect_pain_points(text_content)
        
        # Analyse des valeurs affichées
        values = self._detect_values(text_content)
        
        # Extraction des mots-clés principaux
        keywords = self._extract_keywords(text_content)
        
        # Détection du ton et du style
        tone = self._analyze_tone(text_content)
        
        # Analyse de la structure de contenu
        content_structure = self._analyze_content_structure(html_content)
        
        result = {
            "url": url,
            "text_length": len(text_content),
            "pain_points": pains,
            "values": values,
            "keywords": keywords,
            "tone": tone,
            "content_structure": content_structure,
            "recommendations": self._generate_recommendations(pains, values, keywords)
        }
        
        # Émission d'événement
        if self.event_bus:
            await self.event_bus.publish("semantic.analysis_completed", {
                "url": url,
                "pain_count": len(pains),
                "value_count": len(values),
                "top_keyword": keywords[0] if keywords else None
            })
        
        return result
    
    def _extract_visible_text(self, html: str) -> str:
        """Extrait le texte visible du HTML (sans tags, scripts, styles)"""
        # Suppression des scripts et styles
        text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        # Suppression des tags HTML
        text = re.sub(r'<[^>]+>', ' ', text)
        # Nettoyage des espaces multiples
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def _detect_pain_points(self, text: str) -> List[Dict[str, Any]]:
        """Détecte les douleurs potentielles dans le texte"""
        detected_pains = []
        text_lower = text.lower()
        
        for category, patterns in PAIN_PATTERNS.items():
            matches = []
            for pattern in patterns:
                if pattern in text_lower:
                    # Calcul d'un score simple basé sur la fréquence
                    count = text_lower.count(pattern)
                    if count > 0:
                        matches.append({
                            "keyword": pattern,
                            "count": count,
                            "context": self._get_context(text, pattern)
                        })
            
            if matches:
                detected_pains.append({
                    "category": category,
                    "matches": matches,
                    "severity": min(len(matches) * 0.2, 1.0)  # Score 0-1
                })
        
        # Tri par sévérité
        detected_pains.sort(key=lambda x: x["severity"], reverse=True)
        return detected_pains
    
    def _detect_values(self, text: str) -> List[Dict[str, Any]]:
        """Détecte les valeurs mises en avant par l'entreprise"""
        detected_values = []
        text_lower = text.lower()
        
        for value in VALUE_INDICATORS:
            if value in text_lower:
                count = text_lower.count(value)
                detected_values.append({
                    "value": value,
                    "count": count,
                    "prominence": min(count * 0.3, 1.0)
                })
        
        detected_values.sort(key=lambda x: x["prominence"], reverse=True)
        return detected_values
    
    def _extract_keywords(self, text: str, top_n: int = 10) -> List[str]:
        """Extrait les mots-clés principaux (approche simplifiée sans ML lourd)"""
        # Tokenisation simple
        words = re.findall(r'\b[a-zA-ZÀ-ÿ]{4,}\b', text.lower())
        
        # Stop words français
        stop_words = {
            "le", "la", "les", "un", "une", "des", "du", "de", "et", "ou", "mais",
            "dans", "sur", "pour", "avec", "sans", "par", "plus", "moins", "très",
            "nous", "vous", "ils", "elles", "notre", "votre", "leur", "ceci", "cela"
        }
        
        # Filtrage et comptage
        filtered_words = [w for w in words if w not in stop_words]
        word_counts = Counter(filtered_words)
        
        return [word for word, count in word_counts.most_common(top_n)]
    
    def _analyze_tone(self, text: str) -> Dict[str, float]:
        """Analyse le ton du contenu (formel, technique, commercial, etc.)"""
        text_lower = text.lower()
        
        indicators = {
            "formel": ["madame", "monsieur", "société", "entreprise", "prestataire"],
            "technique": ["API", "SDK", "integration", "architecture", "algorithme"],
            "commercial": ["offre", "promotion", "gratuit", "essai", "contactez"],
            "innovant": ["nouveau", "révolutionnaire", "breakthrough", "premier"],
            "rassurant": ["confiance", "garantie", "sécurisé", "fiable", "prouvé"]
        }
        
        scores = {}
        for tone, words in indicators.items():
            count = sum(1 for word in words if word in text_lower)
            scores[tone] = min(count * 0.15, 1.0)
        
        return scores
    
    def _analyze_content_structure(self, html: str) -> Dict[str, Any]:
        """Analyse la structure du contenu (titres, sections, CTA)"""
        structure = {
            "h1_count": len(re.findall(r'<h1[^>]*>.*?</h1>', html, re.DOTALL | re.IGNORECASE)),
            "h2_count": len(re.findall(r'<h2[^>]*>.*?</h2>', html, re.DOTALL | re.IGNORECASE)),
            "h3_count": len(re.findall(r'<h3[^>]*>.*?</h3>', html, re.DOTALL | re.IGNORECASE)),
            "cta_count": len(re.findall(r'(contactez|demandez|téléchargez|inscrivez|essayez)', html, re.IGNORECASE)),
            "has_video": bool(re.search(r'<video|iframe.*?(youtube|vimeo)', html, re.IGNORECASE)),
            "has_testimonials": bool(re.search(r'(témoignage|avis|client|retour)', html, re.IGNORECASE)),
            "has_case_studies": bool(re.search(r'(cas client|étude de cas|success story)', html, re.IGNORECASE))
        }
        return structure
    
    def _get_context(self, text: str, keyword: str, window: int = 50) -> str:
        """Récupère le contexte autour d'un mot-clé"""
        text_lower = text.lower()
        idx = text_lower.find(keyword)
        if idx == -1:
            return ""
        start = max(0, idx - window)
        end = min(len(text), idx + len(keyword) + window)
        return "..." + text[start:end] + "..."
    
    def _generate_recommendations(self, pains: List, values: List, keywords: List) -> List[str]:
        """Génère des recommandations basées sur l'analyse"""
        recommendations = []
        
        if pains:
            top_pain = pains[0]["category"]
            recommendations.append(f"Aborder la problématique '{top_pain}' identifiée sur leur site")
        
        if values:
            top_value = values[0]["value"]
            recommendations.append(f"S'appuyer sur leur valeur mise en avant: '{top_value}'")
        
        if keywords:
            recommendations.append(f"Utiliser leur vocabulaire clé: {', '.join(keywords[:3])}")
        
        return recommendations

# Factory pour le plugin
def create_plugin(event_bus=None):
    return SemanticAnalyzer(event_bus)
