"""
Plugin Pain Point Engine - Génération d'angles commerciaux basés sur des faits vérifiés
0% hallucination : chaque angle est tracé à un fait observable dans l'audit digital
"""
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from loguru import logger

from core.config import settings
from core.event_bus import event_bus


def get_nested_value(data: Dict[str, Any], key_path: str) -> Any:
    """Extrait une valeur imbriquée depuis un chemin de clés (ex: 'seo.meta_tags.title')"""
    keys = key_path.split('.')
    value = data
    
    for key in keys:
        if isinstance(value, dict):
            value = value.get(key)
        else:
            return None
    
    return value


class RuleEngine:
    """Moteur de règles déterministe pour générer des angles commerciaux"""
    
    def __init__(self, rules_file: Path):
        self.rules_file = rules_file
        self.rules: List[Dict[str, Any]] = []
        self.operators: Dict[str, str] = {}
        self.categories: Dict[str, Dict[str, str]] = {}
        self.priorities: Dict[str, Dict[str, str]] = {}
        self.load_rules()
    
    def load_rules(self):
        """Charge les règles depuis le fichier YAML"""
        try:
            with open(self.rules_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            self.rules = config.get('rules', [])
            self.operators = config.get('operators', {})
            self.categories = config.get('categories', {})
            self.priorities = config.get('priorities', {})
            
            logger.info(f"Loaded {len(self.rules)} rules from {self.rules_file}")
            
        except Exception as e:
            logger.error(f"Failed to load rules: {e}")
            self.rules = []
    
    def evaluate_condition(self, condition: Dict[str, Any], audit_data: Dict[str, Any]) -> bool:
        """
        Évalue une condition contre les données d'audit
        Retourne True si la condition est satisfaite
        """
        fact_key = condition.get('fact')
        operator = condition.get('operator')
        expected_value = condition.get('value')
        
        # Récupère la valeur du fait
        actual_value = get_nested_value(audit_data, fact_key)
        
        # Applique l'opérateur
        if operator == 'not_contains':
            if isinstance(actual_value, list):
                return expected_value not in actual_value
            return expected_value not in str(actual_value) if actual_value else True
        
        elif operator == 'equals':
            return actual_value == expected_value
        
        elif operator == 'is_null':
            return actual_value is None
        
        elif operator == 'is_empty':
            return actual_value is None or actual_value == ""
        
        elif operator == 'is_empty_list':
            return isinstance(actual_value, list) and len(actual_value) == 0
        
        elif operator == 'greater_than':
            try:
                return float(actual_value) > float(expected_value)
            except (TypeError, ValueError):
                return False
        
        elif operator == 'less_than':
            try:
                return float(actual_value) < float(expected_value)
            except (TypeError, ValueError):
                return False
        
        elif operator == 'count_non_null_less_than':
            if isinstance(actual_value, dict):
                non_null_count = sum(1 for v in actual_value.values() if v is not None)
                return non_null_count < expected_value
            return False
        
        return False
    
    def generate_angles(self, audit_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Génère une liste d'angles commerciaux basés sur les règles
        Chaque angle est lié à un fait vérifié dans l'audit
        """
        angles = []
        
        for rule in self.rules:
            try:
                condition = rule.get('condition', {})
                
                # Évalue la condition
                if self.evaluate_condition(condition, audit_data):
                    angle_template = rule.get('angle', {})
                    
                    # Crée l'angle avec toutes les métadonnées
                    angle = {
                        "id": rule.get('id'),
                        "name": rule.get('name'),
                        "title": angle_template.get('title'),
                        "description": angle_template.get('description'),
                        "category": angle_template.get('category'),
                        "category_label": self.categories.get(
                            angle_template.get('category'), {}
                        ).get('label', 'Autre'),
                        "category_icon": self.categories.get(
                            angle_template.get('category'), {}
                        ).get('icon', '📌'),
                        "priority": angle_template.get('priority'),
                        "priority_label": self.priorities.get(
                            angle_template.get('priority'), {}
                        ).get('label', 'Normal'),
                        "priority_color": self.priorities.get(
                            angle_template.get('priority'), {}
                        ).get('color', 'gray'),
                        "score": angle_template.get('score', 50),
                        "evidence_key": angle_template.get('evidence_key'),
                        "evidence_value": get_nested_value(
                            audit_data, 
                            angle_template.get('evidence_key', '')
                        ),
                        "rule_id": rule.get('id'),
                        "generated_at": datetime.utcnow().isoformat()
                    }
                    
                    angles.append(angle)
                    
            except Exception as e:
                logger.warning(f"Error evaluating rule {rule.get('id')}: {e}")
        
        # Trie par score décroissant
        angles.sort(key=lambda x: x['score'], reverse=True)
        
        return angles


class LLMFormatter:
    """Formattage optionnel des angles avec LLM (pour adapter le ton uniquement)"""
    
    def __init__(self, enabled: bool = False):
        self.enabled = enabled
        self.tones = {
            "consultatif": "Ton professionnel et conseil, axé sur l'accompagnement",
            "direct": "Ton franc et direct, axé sur les résultats",
            "empathique": "Ton compréhensif, axé sur les défis du prospect",
            "urgent": "Ton qui souligne l'urgence d'agir"
        }
    
    async def format_angle(
        self, 
        angle: Dict[str, Any], 
        tone: str = "consultatif"
    ) -> str:
        """
        Reformule un angle avec un ton spécifique
        Sans LLM: retourne la description originale
        Avec LLM: utilise un modèle local (Ollama) pour reformuler
        """
        if not self.enabled:
            return angle.get('description', '')
        
        # Implémentation LLM optionnelle (à connecter à Ollama/OpenAI)
        # Pour l'instant, retourne la description originale avec préfixe ton
        base_description = angle.get('description', '')
        tone_label = self.tones.get(tone, tone)
        
        return f"[{tone_label}] {base_description}"


class PainPointEnginePlugin:
    """Plugin principal pour la génération d'angles commerciaux"""
    
    def __init__(self):
        self.rules_file = Path(__file__).parent / "rules.yaml"
        self.rule_engine = RuleEngine(self.rules_file)
        self.llm_formatter = LLMFormatter(enabled=False)
        self.generated_angles: Dict[str, List[Dict[str, Any]]] = {}
    
    def generate_angles_for_audit(
        self, 
        prospect_id: str, 
        audit_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Génère des angles pour un prospect basé sur son audit"""
        logger.info(f"Generating angles for prospect {prospect_id}")
        
        # Extrait les données pertinentes de l'audit
        website_audit = audit_data.get('audit_data', audit_data)
        
        # Génère les angles via le moteur de règles
        angles = self.rule_engine.generate_angles(website_audit)
        
        # Limite le nombre d'angles
        max_angles = 5  # Configurable
        angles = angles[:max_angles]
        
        # Stocke les angles
        self.generated_angles[prospect_id] = angles
        
        # Émet événement
        event_bus.publish("angles.generated", {
            "prospect_id": prospect_id,
            "angles_count": len(angles),
            "top_score": angles[0]['score'] if angles else 0
        })
        
        return angles
    
    def get_angles(self, prospect_id: str) -> List[Dict[str, Any]]:
        """Récupère les angles générés pour un prospect"""
        return self.generated_angles.get(prospect_id, [])
    
    def get_angle_by_id(self, angle_id: str) -> Optional[Dict[str, Any]]:
        """Récupère un angle spécifique par son ID"""
        for angles in self.generated_angles.values():
            for angle in angles:
                if angle.get('id') == angle_id:
                    return angle
        return None
    
    async def format_angle_with_llm(
        self, 
        angle_id: str, 
        tone: str = "consultatif"
    ) -> Dict[str, Any]:
        """Reformule un angle avec un ton spécifique"""
        angle = self.get_angle_by_id(angle_id)
        
        if not angle:
            return {"error": "Angle not found"}
        
        formatted = await self.llm_formatter.format_angle(angle, tone)
        
        event_bus.publish("angle.formatted", {
            "angle_id": angle_id,
            "tone": tone
        })
        
        return {
            "angle_id": angle_id,
            "original": angle.get('description'),
            "formatted": formatted,
            "tone": tone
        }


# Instance globale
plugin_instance = PainPointEnginePlugin()


def init():
    """Initialisation du plugin"""
    logger.info("Initializing pain-point-engine plugin")


def cleanup():
    """Nettoyage du plugin"""
    logger.info("Cleaning up pain-point-engine plugin")


# Handlers API
async def generate_angles(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handler POST /api/v1/angles/generate"""
    prospect_id = request_data.get('prospect_id')
    audit_data = request_data.get('audit_data')
    
    if not prospect_id or not audit_data:
        return {
            "error": "prospect_id and audit_data are required",
            "status_code": 400
        }
    
    angles = plugin_instance.generate_angles_for_audit(prospect_id, audit_data)
    
    return {
        "success": True,
        "prospect_id": prospect_id,
        "angles_count": len(angles),
        "angles": angles
    }


async def get_angles(prospect_id: str) -> Dict[str, Any]:
    """Handler GET /api/v1/angles/{prospect_id}"""
    angles = plugin_instance.get_angles(prospect_id)
    
    if not angles:
        return {
            "error": "No angles found. Generate angles first.",
            "status_code": 404
        }
    
    return {
        "prospect_id": prospect_id,
        "angles": angles
    }


async def format_angle(angle_id: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handler POST /api/v1/angles/{angle_id}/format"""
    tone = request_data.get('tone', 'consultatif')
    
    result = await plugin_instance.format_angle_with_llm(angle_id, tone)
    
    if 'error' in result:
        return {**result, "status_code": 404}
    
    return result
