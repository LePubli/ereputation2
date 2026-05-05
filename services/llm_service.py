"""
Services LLM pour le formatting et l'analyse sémantique
Supporte Ollama (local), OpenAI et Anthropic
Utilisation éthique: formatting uniquement, pas de génération de contenu commercial
"""
import json
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod
from loguru import logger

from core.config import settings


class LLMProvider(ABC):
    """Interface abstraite pour les providers LLM"""
    
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        """Génère une réponse à partir d'un prompt"""
        pass
    
    @abstractmethod
    async def format_json(self, data: Dict[str, Any], template: str) -> Dict[str, Any]:
        """Formate des données selon un template JSON"""
        pass
    
    @abstractmethod
    async def extract_entities(self, text: str) -> Dict[str, Any]:
        """Extrait des entités nommées d'un texte"""
        pass


class OllamaProvider(LLMProvider):
    """Provider pour Ollama (LLM local)"""
    
    def __init__(self, model: str = None, api_url: str = None):
        self.model = model or settings.LLM_MODEL
        self.api_url = api_url or settings.LLM_API_URL
        self.timeout = 60
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Génère une réponse via Ollama"""
        try:
            import httpx
            
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": kwargs.get("temperature", 0.3),
                    "top_p": kwargs.get("top_p", 0.9),
                }
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.api_url}/api/generate",
                    json=payload
                )
                response.raise_for_status()
                
                result = response.json()
                return result.get("response", "")
                
        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
            return ""
    
    async def format_json(self, data: Dict[str, Any], template: str) -> Dict[str, Any]:
        """Formate des données selon un template JSON"""
        prompt = f"""
Tu es un assistant de formatting JSON. Reformate les données suivantes selon ce template:

Template attendu:
{template}

Données à formater:
{json.dumps(data, indent=2, ensure_ascii=False)}

Règles:
- Ne change PAS le sens des données
- Respecte EXACTEMENT la structure du template
- Retourne UNIQUEMENT le JSON valide, sans texte autour
- Si une donnée manque, utilise null ou une valeur par défaut appropriée

JSON formaté:
"""
        try:
            response = await self.generate(prompt, temperature=0.1)
            # Extraction du JSON de la réponse
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
            else:
                logger.warning("No valid JSON found in response")
                return data
        except Exception as e:
            logger.error(f"JSON formatting error: {e}")
            return data
    
    async def extract_entities(self, text: str) -> Dict[str, Any]:
        """Extrait des entités nommées d'un texte"""
        prompt = f"""
Extrais les entités nommées suivantes du texte ci-dessous:
- Entreprises (noms de sociétés)
- Personnes (noms propres)
- Lieux (villes, pays)
- Dates
- Chiffres clés (CA, effectifs, etc.)
- Technologies mentionnées

Texte:
{text}

Retourne UNIQUEMENT un JSON valide avec cette structure:
{{
    "entreprises": [],
    "personnes": [],
    "lieux": [],
    "dates": [],
    "chiffres_cles": [],
    "technologies": []
}}

Extraction:
"""
        try:
            response = await self.generate(prompt, temperature=0.1)
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
            else:
                return {"error": "No valid JSON found"}
        except Exception as e:
            logger.error(f"Entity extraction error: {e}")
            return {"error": str(e)}


class OpenAIProvider(LLMProvider):
    """Provider pour OpenAI API"""
    
    def __init__(self, api_key: str = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key or settings.LLM_API_KEY
        self.model = model
        self.base_url = "https://api.openai.com/v1"
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Génère une réponse via OpenAI"""
        if not self.api_key:
            logger.warning("OpenAI API key not configured")
            return ""
        
        try:
            import httpx
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": kwargs.get("temperature", 0.3),
                "max_tokens": kwargs.get("max_tokens", 1000)
            }
            
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                
                result = response.json()
                return result["choices"][0]["message"]["content"]
                
        except Exception as e:
            logger.error(f"OpenAI generation error: {e}")
            return ""
    
    async def format_json(self, data: Dict[str, Any], template: str) -> Dict[str, Any]:
        """Formate des données selon un template JSON"""
        prompt = f"""Format the following data according to this JSON template. Return ONLY valid JSON.

Template: {template}
Data: {json.dumps(data)}

Formatted JSON:"""
        
        response = await self.generate(prompt, temperature=0.1)
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                return json.loads(response[json_start:json_end])
        except:
            pass
        return data
    
    async def extract_entities(self, text: str) -> Dict[str, Any]:
        """Extrait des entités nommées"""
        prompt = f"""Extract named entities from this text. Return ONLY valid JSON.

Text: {text}

JSON format: {{"entreprises": [], "personnes": [], "lieux": [], "dates": [], "chiffres_cles": [], "technologies": []}}

Entities:"""
        
        response = await self.generate(prompt, temperature=0.1)
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                return json.loads(response[json_start:json_end])
        except:
            pass
        return {"error": "Extraction failed"}


class AnthropicProvider(LLMProvider):
    """Provider pour Anthropic Claude API"""
    
    def __init__(self, api_key: str = None, model: str = "claude-3-haiku-20240307"):
        self.api_key = api_key or settings.LLM_API_KEY
        self.model = model
        self.base_url = "https://api.anthropic.com/v1"
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Génère une réponse via Anthropic"""
        if not self.api_key:
            logger.warning("Anthropic API key not configured")
            return ""
        
        try:
            import httpx
            
            headers = {
                "x-api-key": self.api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            }
            
            payload = {
                "model": self.model,
                "max_tokens": kwargs.get("max_tokens", 1000),
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }
            
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    f"{self.base_url}/messages",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                
                result = response.json()
                return result["content"][0]["text"]
                
        except Exception as e:
            logger.error(f"Anthropic generation error: {e}")
            return ""
    
    async def format_json(self, data: Dict[str, Any], template: str) -> Dict[str, Any]:
        """Formate des données selon un template JSON"""
        # Implémentation similaire à OpenAI
        return await super().format_json(data, template)
    
    async def extract_entities(self, text: str) -> Dict[str, Any]:
        """Extrait des entités nommées"""
        # Implémentation similaire à OpenAI
        return await super().extract_entities(text)


class LLMService:
    """
    Service unifié pour l'accès aux LLM
    Gère le routing vers le provider configuré
    """
    
    def __init__(self, provider: str = None):
        self.provider_name = provider or settings.LLM_PROVIDER
        self.provider = self._create_provider()
    
    def _create_provider(self) -> LLMProvider:
        """Crée le provider configuré"""
        if self.provider_name == "ollama":
            return OllamaProvider()
        elif self.provider_name == "openai":
            return OpenAIProvider()
        elif self.provider_name == "anthropic":
            return AnthropicProvider()
        else:
            logger.warning(f"Unknown provider: {self.provider_name}, falling back to Ollama")
            return OllamaProvider()
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Génère une réponse"""
        return await self.provider.generate(prompt, **kwargs)
    
    async def format_json(self, data: Dict[str, Any], template: str) -> Dict[str, Any]:
        """Formate des données JSON"""
        return await self.provider.format_json(data, template)
    
    async def extract_entities(self, text: str) -> Dict[str, Any]:
        """Extrait des entités"""
        return await self.provider.extract_entities(text)
    
    async def summarize(self, text: str, max_length: int = 200) -> str:
        """Résume un texte"""
        prompt = f"""Résume ce texte en {max_length} caractères maximum:

{text}

Résumé:"""
        return await self.generate(prompt, temperature=0.3)
    
    async def classify_text(self, text: str, categories: List[str]) -> str:
        """Classifie un texte dans une catégorie"""
        prompt = f"""Classe ce texte dans l'une de ces catégories: {', '.join(categories)}

Texte: {text}

Catégorie (réponds seulement par le nom de la catégorie):"""
        return await self.generate(prompt, temperature=0.1)
    
    async def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """Extrait les mots-clés principaux"""
        prompt = f"""Extrais les {max_keywords} mots-clés principaux de ce texte.
Retourne UNIQUEMENT une liste JSON de chaînes.

Texte: {text}

Mots-clés:"""
        response = await self.generate(prompt, temperature=0.1)
        try:
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            if json_start >= 0 and json_end > json_start:
                return json.loads(response[json_start:json_end])
        except:
            pass
        return []


# Instance globale
llm_service = LLMService()


def get_llm_service() -> LLMService:
    """Retourne l'instance du service LLM"""
    return llm_service


def create_llm_provider(provider_type: str = None) -> LLMProvider:
    """Factory pour créer un provider spécifique"""
    provider_name = provider_type or settings.LLM_PROVIDER
    
    if provider_name == "ollama":
        return OllamaProvider()
    elif provider_name == "openai":
        return OpenAIProvider()
    elif provider_name == "anthropic":
        return AnthropicProvider()
    else:
        return OllamaProvider()
