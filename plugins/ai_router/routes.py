"""Plugin AI Router — endpoints multi-LLM avec Claude + Qwen + Groq + Ollama."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import CurrentUser
from core.database import get_db
from services.ai_router import ai_complete, get_available_providers

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])


class AIRequest(BaseModel):
    prompt: str
    system: str | None = None
    mode: str = "agent"                  # agent / email / scoring / research / extract
    provider: str = "auto"               # auto / claude / qwen / groq / ollama
    max_tokens: int = 1500
    use_search: bool = False
    prospect_id: UUID | None = None      # Pour contextualiser automatiquement
    field_to_write: str | None = None    # Si spécifié, écrit dans ai_enrichment


@router.post("/complete")
async def complete(
    body: AIRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Complète un prompt avec le meilleur LLM disponible."""
    # Enrichit le contexte si prospect_id fourni
    context_prefix = ""
    if body.prospect_id:
        from models.database.prospect import Prospect
        p = (await db.execute(select(Prospect).where(Prospect.id == body.prospect_id))).scalar_one_or_none()
        if p:
            context_prefix = f"""ENTREPRISE : {p.company_name}
SIREN : {p.siren or "N/A"} | SIRET : {p.siret or "N/A"}
VILLE : {p.city or "N/A"} | CODE NAF : {p.naf_code or "N/A"} — {p.naf_label or ""}
EFFECTIFS : {p.employee_range or "N/A"} | SITE WEB : {p.website or "N/A"}
ENRICHISSEMENT : {str(p.enrichment or {})[:400]}

INSTRUCTION : """

    full_prompt = context_prefix + body.prompt

    result = await ai_complete(
        prompt=full_prompt,
        system=body.system,
        mode=body.mode,
        provider=body.provider,
        max_tokens=body.max_tokens,
        use_search=body.use_search,
    )

    if not result.success:
        raise HTTPException(status_code=503, detail="Aucun provider AI disponible. Configurez au moins QWEN_API_KEY (gratuit) dans Coolify.")

    # Écrit dans ai_enrichment si field_to_write spécifié
    if body.field_to_write and body.prospect_id and result.content:
        from models.database.prospect import Prospect
        p = (await db.execute(select(Prospect).where(Prospect.id == body.prospect_id))).scalar_one_or_none()
        if p:
            ai_data = dict(p.ai_enrichment or {})
            parsed = result.json()
            value = parsed.get("result") if parsed else result.content[:200]
            ai_data[body.field_to_write] = {
                "value": value,
                "provider": result.provider,
                "model": result.model,
                "confidence": parsed.get("confidence", 0.7) if parsed else 0.5,
                "reasoning": parsed.get("reasoning", "") if parsed else "",
                "tokens": result.tokens_total,
            }
            p.ai_enrichment = ai_data
            await db.commit()

    return {
        **result.to_dict(),
        "json_parsed": result.json(),
        "field_written": body.field_to_write,
    }


@router.get("/providers")
async def providers(current_user: CurrentUser):
    """Liste tous les providers AI avec leur statut et pricing."""
    return {"providers": await get_available_providers()}


@router.post("/generate-email")
async def generate_email(
    prospect_id: UUID,
    step_type: str = "first_contact",
    provider: str = "auto",
    current_user: CurrentUser = Depends(lambda: None),
    db: AsyncSession = Depends(get_db),
):
    """Génère un email commercial personnalisé pour un prospect."""
    from models.database.prospect import Prospect
    p = (await db.execute(select(Prospect).where(Prospect.id == prospect_id))).scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404)

    contact = p.contacts[0] if p.contacts else None
    first_name = contact.first_name if contact else "Madame/Monsieur"

    prompts = {
        "first_contact": f"""Écris un email de premier contact B2B pour {p.company_name} basée à {p.city or 'France'} ({p.naf_label or 'secteur inconnu'}).
Contact : {first_name} {contact.last_name if contact else ''} {f'— {contact.role}' if contact and contact.role else ''}
Site web : {p.website or 'non renseigné'} | Effectifs : {p.employee_range or 'inconnu'}

L'email doit :
- Mentionner un détail spécifique sur l'entreprise
- Proposer une valeur concrète (agence digitale, SEO, web, automatisation)
- Être court (5-7 lignes max)
- Avoir un appel à l'action clair
- Ton professionnel mais chaleureux

Format JSON : {{"subject": "...", "body": "...", "ps": "..."}}""",

        "followup": f"""Écris un email de relance (J+3) pour {p.company_name}. Court, direct, rappelle brièvement la valeur sans être insistant.
Format JSON : {{"subject": "Re: ...", "body": "..."}}""",

        "breakup": f"""Écris un email de break-up pour {p.company_name}. Élégant, laisse une porte ouverte.
Format JSON : {{"subject": "...", "body": "..."}}""",
    }

    result = await ai_complete(
        prompt=prompts.get(step_type, prompts["first_contact"]),
        mode="email",
        provider=provider,
    )

    parsed = result.json()
    return {
        "prospect_id": str(prospect_id),
        "step_type": step_type,
        "provider": result.provider,
        "model": result.model,
        "tokens": result.tokens_total,
        "email": parsed or {"subject": "", "body": result.content},
    }


@router.post("/auto-score/{prospect_id}")
async def auto_score(
    prospect_id: UUID,
    provider: str = "auto",
    current_user: CurrentUser = Depends(lambda: None),
    db: AsyncSession = Depends(get_db),
):
    """Score IA enrichi (complémentaire au scoring algorithmique)."""
    from models.database.prospect import Prospect
    from services.scoring import compute_score

    p = (await db.execute(select(Prospect).where(Prospect.id == prospect_id))).scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404)

    # Score algorithmique
    algo_score, algo_cat, algo_details = compute_score(p)

    # Score IA
    prompt = f"""Analyse cette entreprise et évalue sa propension à acheter des services digitaux (web, SEO, automatisation).

Données :
- Entreprise : {p.company_name}
- Secteur : {p.naf_label or "N/A"} ({p.naf_code or "N/A"})
- Ville : {p.city or "N/A"} | Effectifs : {p.employee_range or "N/A"}
- Site web : {"Oui" if p.website else "Non"} | Tél : {"Oui" if p.phone else "Non"}
- Score algorithmique actuel : {algo_score}/100 ({algo_cat})
- Sources données : {', '.join(p.sources_used or [])}
- Tags : {', '.join(p.tags or [])}
- Signaux BODACC : {str((p.enrichment or {}).get('bodacc_signals', {}))}

Évalue et retourne JSON : {{"score": <0-100>, "category": "HOT|WARM|COLD", "reasoning": "<2 phrases>", "key_signals": ["...", "..."], "recommended_action": "<action concrète>"}}"""

    result = await ai_complete(prompt=prompt, mode="scoring", provider=provider)
    parsed = result.json() or {}

    ai_score = parsed.get("score", algo_score)
    ai_cat = parsed.get("category", algo_cat)
    combined_score = round((algo_score * 0.6) + (ai_score * 0.4))

    # Mise à jour
    p.propensity_score = combined_score
    p.propensity_category = ai_cat if parsed else algo_cat
    p.scoring_details = {
        **algo_details,
        "ai_score": ai_score,
        "ai_category": ai_cat,
        "ai_reasoning": parsed.get("reasoning", ""),
        "ai_signals": parsed.get("key_signals", []),
        "recommended_action": parsed.get("recommended_action", ""),
        "ai_provider": result.provider,
        "combined_score": combined_score,
    }
    await db.commit()

    return {
        "prospect_id": str(prospect_id),
        "algo_score": algo_score,
        "ai_score": ai_score,
        "combined_score": combined_score,
        "category": p.propensity_category,
        "provider": result.provider,
        **parsed,
    }
