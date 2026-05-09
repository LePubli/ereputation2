"""
AI Router — Multi-LLM autonome avec fallback.

Providers supportés (par ordre de priorité) :
    1. Claude (Anthropic) — ANTHROPIC_API_KEY
    2. Qwen (Alibaba)     — QWEN_API_KEY  ← NOUVEAU, gratuit avec quota
    3. Groq (Llama)       — GROQ_API_KEY  ← ultra-rapide, gratuit
    4. Ollama (local)     — OLLAMA_URL    ← 100% gratuit, sur serveur

Qwen modèles disponibles (2026) :
    qwen-turbo     → gratuit, 1M tokens/mois, très rapide
    qwen-plus      → payant, très bon rapport qualité/prix
    qwen-max       → payant, GPT-4 level
    qwen-long      → 10M context window

Logique de fallback :
    Si Claude échoue → essaie Qwen → essaie Groq → erreur
    Si quota dépassé → next provider automatiquement

Usage :
    result = await ai_complete(prompt="...", mode="agent")
    result = await ai_complete(prompt="...", mode="email", provider="qwen")
"""
from __future__ import annotations

import json
import re
import time
from typing import Any

import httpx
from loguru import logger

from core.config import settings


# ─── Schemas ─────────────────────────────────────────────────────────────────

class AIResponse:
    def __init__(
        self,
        content: str,
        provider: str,
        model: str,
        tokens_in: int = 0,
        tokens_out: int = 0,
        duration_ms: int = 0,
        cost_usd: float = 0.0,
    ):
        self.content = content
        self.provider = provider
        self.model = model
        self.tokens_in = tokens_in
        self.tokens_out = tokens_out
        self.tokens_total = tokens_in + tokens_out
        self.duration_ms = duration_ms
        self.cost_usd = cost_usd
        self.success = bool(content)

    def json(self) -> dict[str, Any] | None:
        """Tente de parser le contenu comme JSON."""
        try:
            match = re.search(r'\{[\s\S]*\}', self.content)
            if match:
                return json.loads(match.group())
        except Exception:
            pass
        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "content": self.content,
            "provider": self.provider,
            "model": self.model,
            "tokens_total": self.tokens_total,
            "duration_ms": self.duration_ms,
            "cost_usd": round(self.cost_usd, 6),
        }


# ─── Providers ────────────────────────────────────────────────────────────────

async def _call_claude(
    system: str,
    user: str,
    max_tokens: int = 1500,
    tools: list | None = None,
) -> AIResponse:
    """Anthropic Claude API."""
    api_key = getattr(settings, "ANTHROPIC_API_KEY", "")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY manquante")

    payload: dict[str, Any] = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": max_tokens,
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }
    if tools:
        payload["tools"] = tools

    start = time.time()
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()

    content = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
    usage = data.get("usage", {})
    dur = int((time.time() - start) * 1000)

    ti = usage.get("input_tokens", 0)
    to = usage.get("output_tokens", 0)
    cost = (ti * 3e-6) + (to * 15e-6)  # Sonnet pricing

    return AIResponse(content, "claude", "claude-sonnet-4-20250514", ti, to, dur, cost)


async def _call_qwen(
    system: str,
    user: str,
    max_tokens: int = 1500,
    model: str = "qwen-turbo",
) -> AIResponse:
    """
    Alibaba Qwen API — compatible OpenAI format.
    qwen-turbo : GRATUIT avec 1M tokens/mois
    Endpoint : https://dashscope.aliyuncs.com/compatible-mode/v1
    """
    api_key = getattr(settings, "QWEN_API_KEY", "")
    if not api_key:
        raise ValueError("QWEN_API_KEY manquante")

    start = time.time()
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "max_tokens": max_tokens,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "stream": False,
            },
        )
        resp.raise_for_status()
        data = resp.json()

    content = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})
    dur = int((time.time() - start) * 1000)
    ti = usage.get("prompt_tokens", 0)
    to = usage.get("completion_tokens", 0)

    # Qwen-turbo : ~$0.002/1M input, $0.006/1M output
    cost = (ti * 2e-9) + (to * 6e-9)

    return AIResponse(content, "qwen", model, ti, to, dur, cost)


async def _call_groq(
    system: str,
    user: str,
    max_tokens: int = 1500,
    model: str = "llama-3.3-70b-versatile",
) -> AIResponse:
    """
    Groq — Llama ultra-rapide, plan gratuit généreux.
    6000 req/min, 500k tokens/jour gratuit.
    """
    api_key = getattr(settings, "GROQ_API_KEY", "")
    if not api_key:
        raise ValueError("GROQ_API_KEY manquante")

    start = time.time()
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "max_tokens": max_tokens,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            },
        )
        resp.raise_for_status()
        data = resp.json()

    content = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})
    dur = int((time.time() - start) * 1000)

    return AIResponse(content, "groq", model, usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0), dur, 0.0)


async def _call_ollama(
    system: str,
    user: str,
    max_tokens: int = 1500,
    model: str = "mistral",
) -> AIResponse:
    """Ollama local — 100% gratuit, sur le même serveur Ubuntu."""
    base_url = getattr(settings, "OLLAMA_URL", "http://localhost:11434")
    start = time.time()
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            f"{base_url}/api/chat",
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "stream": False,
            },
        )
        resp.raise_for_status()
        data = resp.json()

    content = data.get("message", {}).get("content", "")
    dur = int((time.time() - start) * 1000)
    return AIResponse(content, "ollama", model, 0, 0, dur, 0.0)


# ─── SYSTEM PROMPTS ───────────────────────────────────────────────────────────

SYSTEM_PROMPTS = {
    "agent": """Tu es un agent commercial B2B expert en recherche d'informations sur les entreprises françaises.
Réponds TOUJOURS en JSON valide avec : {"result": <valeur>, "confidence": <0-1>, "source": <string>, "reasoning": <string>}
Si une info est introuvable, retourne null pour result. Sois factuel, pas spéculatif. Valeurs numériques en chiffres.""",

    "email": """Tu es un expert en copywriting B2B. Tu écris des emails commerciaux personnalisés, naturels, courts et percutants.
Adapte le ton au profil de l'entreprise. Jamais de formules génériques. Toujours un angle de valeur spécifique.""",

    "scoring": """Tu es un expert en qualification commerciale B2B. Tu analyses les données d'une entreprise et évalues sa propension à acheter des services digitaux.
Réponds TOUJOURS en JSON : {"score": <0-100>, "category": "HOT|WARM|COLD", "reasoning": <string>, "key_signals": [<list>]}""",

    "research": """Tu es un analyste business senior. Tu recherches et synthétises des informations sur des entreprises françaises.
Sois précis, factuel et cite tes sources. Si tu ne trouves pas, dis-le clairement.""",

    "extract": """Tu es un extracteur de données structurées. Tu lis du texte et en extrais des informations spécifiques.
Réponds TOUJOURS en JSON strict sans markdown.""",
}


# ─── ROUTER PRINCIPAL ─────────────────────────────────────────────────────────

async def ai_complete(
    prompt: str,
    system: str | None = None,
    mode: str = "agent",
    provider: str = "auto",
    max_tokens: int = 1500,
    use_search: bool = False,
) -> AIResponse:
    """
    Complète un prompt en choisissant le meilleur provider disponible.

    Args:
        prompt:     Message utilisateur
        system:     System prompt (override du mode)
        mode:       "agent" | "email" | "scoring" | "research" | "extract"
        provider:   "auto" | "claude" | "qwen" | "groq" | "ollama"
        max_tokens: Limite de tokens en sortie
        use_search: Active le web search (Claude uniquement)

    Returns:
        AIResponse avec content, provider, tokens, cost
    """
    sys_prompt = system or SYSTEM_PROMPTS.get(mode, SYSTEM_PROMPTS["agent"])

    # Ordre de priorité selon provider demandé
    if provider == "claude":
        providers_to_try = ["claude"]
    elif provider == "qwen":
        providers_to_try = ["qwen"]
    elif provider == "groq":
        providers_to_try = ["groq"]
    elif provider == "ollama":
        providers_to_try = ["ollama"]
    else:
        # Auto : essaie dans l'ordre des clés disponibles
        providers_to_try = []
        if getattr(settings, "ANTHROPIC_API_KEY", ""):
            providers_to_try.append("claude")
        if getattr(settings, "QWEN_API_KEY", ""):
            providers_to_try.append("qwen")
        if getattr(settings, "GROQ_API_KEY", ""):
            providers_to_try.append("groq")
        if getattr(settings, "OLLAMA_URL", ""):
            providers_to_try.append("ollama")
        if not providers_to_try:
            providers_to_try = ["qwen"]  # Qwen avec clé gratuite par défaut

    last_error = None
    tools = [{"type": "web_search_20250305", "name": "web_search"}] if use_search and "claude" in providers_to_try else None

    for p in providers_to_try:
        try:
            logger.debug(f"[AIRouter] Trying {p} for mode={mode}")
            if p == "claude":
                result = await _call_claude(sys_prompt, prompt, max_tokens, tools)
            elif p == "qwen":
                qwen_model = getattr(settings, "QWEN_MODEL", "qwen-turbo")
                result = await _call_qwen(sys_prompt, prompt, max_tokens, qwen_model)
            elif p == "groq":
                result = await _call_groq(sys_prompt, prompt, max_tokens)
            elif p == "ollama":
                result = await _call_ollama(sys_prompt, prompt, max_tokens)
            else:
                continue

            if result.content:
                logger.info(f"[AIRouter] ✓ {p} | {result.tokens_total} tokens | {result.duration_ms}ms")
                return result

        except Exception as e:
            last_error = e
            logger.warning(f"[AIRouter] {p} failed: {e}")
            continue

    # Tous les providers ont échoué
    logger.error(f"[AIRouter] All providers failed. Last: {last_error}")
    return AIResponse(
        content="",
        provider="none",
        model="",
        duration_ms=0,
    )


async def get_available_providers() -> list[dict]:
    """Retourne la liste des providers disponibles avec leur statut."""
    providers = [
        {
            "id": "claude",
            "name": "Claude Sonnet",
            "vendor": "Anthropic",
            "active": bool(getattr(settings, "ANTHROPIC_API_KEY", "")),
            "free": False,
            "price": "$3/1M input — $15/1M output",
            "speed": "medium",
            "quality": "excellent",
            "env_key": "ANTHROPIC_API_KEY",
            "models": ["claude-sonnet-4-20250514", "claude-opus-4-6"],
            "features": ["web_search", "tool_use", "vision"],
        },
        {
            "id": "qwen",
            "name": "Qwen Turbo",
            "vendor": "Alibaba Cloud",
            "active": bool(getattr(settings, "QWEN_API_KEY", "")),
            "free": True,
            "free_quota": "1M tokens/mois gratuit",
            "price": "$0.002/1M input — $0.006/1M output",
            "speed": "fast",
            "quality": "very_good",
            "env_key": "QWEN_API_KEY",
            "models": ["qwen-turbo", "qwen-plus", "qwen-max", "qwen-long"],
            "features": ["long_context"],
            "signup_url": "https://dashscope.console.aliyun.com/",
        },
        {
            "id": "groq",
            "name": "Llama 3.3 70B (Groq)",
            "vendor": "Groq",
            "active": bool(getattr(settings, "GROQ_API_KEY", "")),
            "free": True,
            "free_quota": "500k tokens/jour gratuit",
            "price": "Gratuit (limité)",
            "speed": "ultra_fast",
            "quality": "good",
            "env_key": "GROQ_API_KEY",
            "models": ["llama-3.3-70b-versatile", "mixtral-8x7b-32768"],
            "features": ["ultra_fast_inference"],
            "signup_url": "https://console.groq.com/",
        },
        {
            "id": "ollama",
            "name": "Ollama (local)",
            "vendor": "Meta / Mistral / etc.",
            "active": bool(getattr(settings, "OLLAMA_URL", "")),
            "free": True,
            "free_quota": "Illimité (sur votre serveur)",
            "price": "0€ — modèles locaux",
            "speed": "variable",
            "quality": "good",
            "env_key": "OLLAMA_URL",
            "models": ["mistral", "llama3", "qwen2.5"],
            "features": ["privacy", "unlimited"],
            "signup_url": "https://ollama.ai/",
        },
    ]
    return providers
