"""
AI Agent — Copilote commercial via Claude API.

Fonctionnement Clay-style :
    1. L'utilisateur définit une colonne avec un prompt
       ex: "Quel est le CA de cette entreprise ?"
    2. L'agent recherche les infos (via web_search tool)
    3. Retourne la valeur + source + confiance

Usage :
    result = await run_agent(
        prospect=prospect,
        prompt="Trouve le chiffre d'affaires et le nombre d'employés",
        field="ca_employees"
    )
"""
import json
import time
from typing import Any

import httpx
from loguru import logger

from core.config import settings


SYSTEM_PROMPT = """Tu es un agent commercial B2B expert en recherche d'informations sur les entreprises françaises.

Pour chaque entreprise, tu dois :
1. Analyser les informations déjà disponibles
2. Rechercher des informations complémentaires si nécessaire
3. Retourner uniquement les informations demandées, sous forme structurée

RÈGLES :
- Réponds TOUJOURS en JSON valide
- Si une info est introuvable, retourne null pour ce champ
- Cite tes sources
- Sois factuel, pas spéculatif
- Toutes les valeurs numériques en chiffres (pas de texte)

FORMAT DE RÉPONSE (JSON strict) :
{
  "result": <valeur trouvée>,
  "confidence": <float 0-1>,
  "source": <string>,
  "reasoning": <string court>
}"""


async def run_agent(
    prospect_data: dict[str, Any],
    prompt: str,
    use_search: bool = True,
    anthropic_api_key: str | None = None,
) -> dict[str, Any]:
    """
    Lance l'agent Claude sur un prospect avec un prompt donné.

    Args:
        prospect_data: Données du prospect (company_name, siren, city, etc.)
        prompt: Question / instruction de l'utilisateur
        use_search: Activer la recherche web (tool use)
        anthropic_api_key: Clé API Anthropic (depuis settings si None)

    Returns:
        dict avec result, confidence, source, reasoning, tokens_used, duration_ms
    """
    api_key = anthropic_api_key or getattr(settings, "ANTHROPIC_API_KEY", "")
    if not api_key:
        return {
            "result": None,
            "confidence": 0,
            "source": "error",
            "reasoning": "ANTHROPIC_API_KEY non configurée",
            "tokens_used": 0,
            "duration_ms": 0,
            "error": "missing_api_key",
        }

    # Contexte prospect pour l'agent
    context = f"""
ENTREPRISE : {prospect_data.get('company_name', 'Inconnue')}
SIREN : {prospect_data.get('siren', 'N/A')}
SIRET : {prospect_data.get('siret', 'N/A')}
VILLE : {prospect_data.get('city', 'N/A')}
CODE POSTAL : {prospect_data.get('postal_code', 'N/A')}
CODE NAF : {prospect_data.get('naf_code', 'N/A')} — {prospect_data.get('naf_label', '')}
FORME JURIDIQUE : {prospect_data.get('legal_form', 'N/A')}
EFFECTIFS : {prospect_data.get('employee_range', 'N/A')}
SITE WEB : {prospect_data.get('website', 'N/A')}
DONNÉES ENRICHIES : {json.dumps(prospect_data.get('enrichment', {}), ensure_ascii=False)[:500]}
"""

    user_message = f"""
{context}

INSTRUCTION : {prompt}

Réponds en JSON strict selon le format demandé.
"""

    tools = [
        {
            "type": "web_search_20250305",
            "name": "web_search",
        }
    ] if use_search else []

    payload: dict[str, Any] = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 1000,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": user_message}],
    }
    if tools:
        payload["tools"] = tools

    start = time.time()
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

    except Exception as e:
        logger.warning(f"[Agent] Erreur API Claude : {e}")
        return {
            "result": None, "confidence": 0,
            "source": "error", "reasoning": str(e),
            "tokens_used": 0, "duration_ms": int((time.time() - start) * 1000),
            "error": str(e),
        }

    duration_ms = int((time.time() - start) * 1000)
    tokens = data.get("usage", {})
    tokens_used = tokens.get("input_tokens", 0) + tokens.get("output_tokens", 0)

    # Extraire le texte de la réponse
    raw_text = ""
    for block in data.get("content", []):
        if block.get("type") == "text":
            raw_text += block.get("text", "")

    # Parser le JSON retourné par l'agent
    try:
        # Extraire le JSON du texte (l'agent peut mettre du texte autour)
        import re
        json_match = re.search(r'\{[\s\S]*\}', raw_text)
        if json_match:
            result_data = json.loads(json_match.group())
        else:
            result_data = {"result": raw_text.strip(), "confidence": 0.5, "source": "claude", "reasoning": ""}
    except json.JSONDecodeError:
        result_data = {"result": raw_text.strip(), "confidence": 0.5, "source": "claude", "reasoning": ""}

    return {
        **result_data,
        "tokens_used": tokens_used,
        "duration_ms": duration_ms,
        "raw_response": raw_text[:500],
    }


async def bulk_agent_enrich(
    prospects: list[dict[str, Any]],
    prompt: str,
    api_key: str | None = None,
    max_concurrent: int = 3,
) -> list[dict[str, Any]]:
    """Lance l'agent sur plusieurs prospects en parallèle (max 3 concurrent)."""
    import asyncio
    semaphore = asyncio.Semaphore(max_concurrent)

    async def enrich_one(p: dict) -> dict:
        async with semaphore:
            result = await run_agent(p, prompt, api_key=api_key)
            return {"prospect_id": p.get("id"), **result}

    return await asyncio.gather(*[enrich_one(p) for p in prospects])
