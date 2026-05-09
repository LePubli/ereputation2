"""
Plugin Contact Intelligence — Endpoints Apollo-style.

Endpoints :
    POST /api/v1/contacts/find          → Recherche contact sur un prospect
    POST /api/v1/contacts/find-bulk     → Recherche en masse (max 50)
    GET  /api/v1/contacts/providers     → Liste les providers actifs
    POST /api/v1/contacts/verify-email  → Vérifie un email via SMTP
    POST /api/v1/contacts/domain-search → Tous les emails d'un domaine
    POST /api/v1/contacts/apply/{id}    → Applique les résultats au prospect
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import CurrentUser
from core.config import settings
from core.database import get_db
from services.contact_intel.router import find_contact
from services.contact_intel.pattern_finder import verify_email_smtp, extract_domain
from services.contact_intel.website_extractor import extract_from_website
from services.contact_intel.api_providers import hunter_domain_search

router = APIRouter(prefix="/api/v1/contacts", tags=["contacts"])


class FindContactRequest(BaseModel):
    prospect_id: UUID | None = None
    company_name: str
    website: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    job_title: str | None = None
    stop_on_verified: bool = True


class BulkFindRequest(BaseModel):
    prospect_ids: list[UUID]
    job_title: str | None = None
    stop_on_verified: bool = True


class VerifyEmailRequest(BaseModel):
    email: str


class DomainSearchRequest(BaseModel):
    domain: str
    use_hunter: bool = False


@router.post("/find")
async def find_contact_endpoint(
    body: FindContactRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """
    Recherche de contact Apollo-style sur une entreprise.
    Waterfall : site web → pattern SMTP → Hunter → Dropcontact → Apollo...
    """
    result = await find_contact(
        company_name=body.company_name,
        website=body.website,
        first_name=body.first_name,
        last_name=body.last_name,
        job_title=body.job_title,
        prospect_id=str(body.prospect_id) if body.prospect_id else None,
        stop_on_verified=body.stop_on_verified,
    )
    return result.to_dict()


@router.post("/find-bulk")
async def bulk_find(
    body: BulkFindRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Lance la recherche de contact sur plusieurs prospects en parallèle."""
    from models.database.prospect import Prospect
    import asyncio

    if len(body.prospect_ids) > 50:
        raise HTTPException(status_code=400, detail="Max 50 prospects en bulk")

    prospects = (await db.execute(
        select(Prospect).where(Prospect.id.in_(body.prospect_ids))
    )).scalars().all()

    semaphore = asyncio.Semaphore(5)  # max 5 en parallèle

    async def enrich_one(p):
        async with semaphore:
            # Prend le premier contact comme référence
            contact = p.contacts[0] if p.contacts else None
            result = await find_contact(
                company_name=p.company_name,
                website=p.website,
                first_name=contact.first_name if contact else None,
                last_name=contact.last_name if contact else None,
                job_title=body.job_title,
                prospect_id=str(p.id),
            )

            # Applique automatiquement si email trouvé
            if result.email and not p.email:
                p.email = result.email
                p.phone = p.phone or result.phone
            if result.all_phones and not p.phone:
                p.phone = result.all_phones[0]

            return result.to_dict()

    results = await asyncio.gather(*[enrich_one(p) for p in prospects], return_exceptions=True)
    await db.commit()

    successful = [r for r in results if isinstance(r, dict)]
    errors = [str(r) for r in results if isinstance(r, Exception)]

    return {
        "processed": len(prospects),
        "enriched": sum(1 for r in successful if r.get("contact", {}).get("email")),
        "errors": errors[:5],
        "results": successful,
    }


@router.post("/apply/{prospect_id}")
async def apply_to_prospect(
    prospect_id: UUID,
    body: FindContactRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Recherche + applique les données contact au prospect en BDD."""
    from models.database.prospect import Prospect, Contact

    prospect = (await db.execute(
        select(Prospect).where(Prospect.id == prospect_id)
    )).scalar_one_or_none()
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect introuvable")

    result = await find_contact(
        company_name=body.company_name or prospect.company_name,
        website=body.website or prospect.website,
        first_name=body.first_name,
        last_name=body.last_name,
        job_title=body.job_title,
        prospect_id=str(prospect_id),
    )

    # Mise à jour du prospect
    if result.email and not prospect.email:
        prospect.email = result.email
    if result.phone and not prospect.phone:
        prospect.phone = result.phone
    if result.all_phones and not prospect.phone:
        prospect.phone = result.all_phones[0]
    if result.linkedin_company:
        enrichment = dict(prospect.enrichment or {})
        enrichment["linkedin_company"] = result.linkedin_company
        prospect.enrichment = enrichment

    # Ajout du contact s'il n'existe pas
    if (result.first_name or result.last_name) and result.email:
        existing = any(
            c.email == result.email for c in (prospect.contacts or [])
        )
        if not existing:
            contact = Contact(
                prospect_id=prospect_id,
                first_name=result.first_name,
                last_name=result.last_name,
                role=result.job_title,
                email=result.email,
                phone=result.phone or result.mobile,
                linkedin_url=result.linkedin_url,
                is_primary=len(prospect.contacts or []) == 0,
            )
            db.add(contact)

    await db.commit()
    return {
        "applied": True,
        "prospect_id": str(prospect_id),
        **result.to_dict(),
    }


@router.post("/verify-email")
async def verify_email(
    body: VerifyEmailRequest,
    current_user: CurrentUser,
):
    """Vérifie un email via SMTP handshake (sans envoyer d'email)."""
    is_valid = await verify_email_smtp(body.email, timeout=6.0)
    return {
        "email": body.email,
        "valid": is_valid,
        "method": "smtp_handshake",
    }


@router.post("/domain-search")
async def domain_search(
    body: DomainSearchRequest,
    current_user: CurrentUser,
):
    """
    Trouve tous les emails connus pour un domaine.
    Gratuit : scrape le site web.
    Avec Hunter API : retourne jusqu'à 100 emails.
    """
    results = []
    sources_used = []

    # Gratuit : extraction site web
    website = f"https://{body.domain}"
    web_data = await extract_from_website(website, body.domain, max_pages=5)
    if web_data["emails"]:
        sources_used.append("website")
        results += [{"email": e, "source": "website", "verified": False} for e in web_data["emails"]]

    # Hunter si demandé et configuré
    hunter_key = getattr(settings, "HUNTER_API_KEY", "")
    if body.use_hunter and hunter_key:
        hunter_contacts = await hunter_domain_search(body.domain, hunter_key, limit=20)
        sources_used.append("hunter")
        for c in hunter_contacts:
            if c.email:
                results.append({
                    "email": c.email,
                    "first_name": c.first_name,
                    "last_name": c.last_name,
                    "job_title": c.job_title,
                    "linkedin": c.linkedin_url,
                    "confidence": c.confidence,
                    "verified": c.verified,
                    "source": "hunter",
                })

    return {
        "domain": body.domain,
        "emails_found": len(results),
        "sources_used": sources_used,
        "results": results,
    }


@router.get("/providers")
async def list_providers(current_user: CurrentUser):
    """Liste les providers actifs (avec ou sans clé API)."""
    providers = [
        {
            "name": "Website Extractor",
            "type": "free",
            "active": True,
            "description": "Extrait emails et téléphones depuis le site web de l'entreprise",
            "config_key": None,
        },
        {
            "name": "Pattern Finder + SMTP",
            "type": "free",
            "active": True,
            "description": "Génère les patterns d'email probables et les vérifie via SMTP",
            "config_key": None,
        },
        {
            "name": "Hunter.io",
            "type": "paid",
            "active": bool(getattr(settings, "HUNTER_API_KEY", "")),
            "description": "Email finder par domaine. 50 req/mois gratuit, $49/mois pour 500.",
            "config_key": "HUNTER_API_KEY",
            "pricing": "50 gratuit/mois, puis $49/mois",
            "url": "https://hunter.io",
        },
        {
            "name": "Dropcontact",
            "type": "paid",
            "active": bool(getattr(settings, "DROPCONTACT_API_KEY", "")),
            "description": "RGPD-compliant, spécialisé France. Excellent pour les PME françaises.",
            "config_key": "DROPCONTACT_API_KEY",
            "pricing": "~0.02€/contact",
            "url": "https://dropcontact.io",
        },
        {
            "name": "Apollo.io",
            "type": "paid",
            "active": bool(getattr(settings, "APOLLO_API_KEY", "")),
            "description": "Base de 275M contacts. 200 req/mois gratuit.",
            "config_key": "APOLLO_API_KEY",
            "pricing": "200 gratuit/mois, puis $49/mois",
            "url": "https://apollo.io",
        },
        {
            "name": "Snov.io",
            "type": "paid",
            "active": bool(getattr(settings, "SNOVIO_CLIENT_ID", "")),
            "description": "Email finder et vérificateur. 150 req/mois gratuit.",
            "config_key": "SNOVIO_CLIENT_ID",
            "pricing": "150 gratuit/mois, puis $39/mois",
            "url": "https://snov.io",
        },
        {
            "name": "Datagma",
            "type": "paid",
            "active": bool(getattr(settings, "DATAGMA_API_KEY", "")),
            "description": "Numéros mobiles depuis LinkedIn. Spécialisé France.",
            "config_key": "DATAGMA_API_KEY",
            "pricing": "~$0.10/numéro mobile",
            "url": "https://datagma.com",
        },
    ]

    return {
        "providers": providers,
        "active_count": sum(1 for p in providers if p["active"]),
        "free_active": sum(1 for p in providers if p["active"] and p["type"] == "free"),
        "paid_active": sum(1 for p in providers if p["active"] and p["type"] == "paid"),
    }
