"""
Adaptateurs APIs payantes — désactivés par défaut, activables via .env.

Configuration dans .env :
    HUNTER_API_KEY=xxx          → Hunter.io (50 req/mois gratuit)
    DROPCONTACT_API_KEY=xxx     → Dropcontact (France, RGPD, ~0.02€/contact)
    APOLLO_API_KEY=xxx          → Apollo.io (200 req/mois gratuit)
    SNOVIO_API_KEY=xxx          → Snov.io (150 req/mois gratuit)
    KASPR_API_KEY=xxx           → Kaspr (LinkedIn mobile numbers)
    DATAGMA_API_KEY=xxx         → Datagma (numéros FR)

Chaque provider est un adaptateur indépendant.
Le ContactIntelRouter essaie les providers dans l'ordre de priorité.

Tarifs indicatifs 2026 :
    Hunter.io      : 50 free/mois, puis $49/mois pour 500 recherches
    Dropcontact    : ~0.02€/enrichissement, RGPD-compliant, France+
    Apollo.io      : 200 free/mois, puis $49/mois pour 10 000
    Snov.io        : 150 free/mois, puis $39/mois
    Datagma        : $0.10/numéro mobile, spécialisé France
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

import httpx
from loguru import logger


@dataclass
class ProviderResult:
    provider: str
    email: str | None = None
    phone: str | None = None
    mobile: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    job_title: str | None = None
    linkedin_url: str | None = None
    confidence: float = 0.0
    verified: bool = False
    raw: dict = None

    def __post_init__(self):
        if self.raw is None:
            self.raw = {}


# =============================================================================
# HUNTER.IO
# =============================================================================

async def hunter_find_email(
    first_name: str,
    last_name: str,
    domain: str,
    api_key: str,
) -> ProviderResult:
    """Hunter.io — Email Finder par prénom + nom + domaine."""
    url = "https://api.hunter.io/v2/email-finder"
    params = {
        "domain": domain,
        "first_name": first_name,
        "last_name": last_name,
        "api_key": api_key,
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, params=params)
            data = resp.json()

        if resp.status_code == 200:
            d = data.get("data", {})
            return ProviderResult(
                provider="hunter",
                email=d.get("email"),
                confidence=d.get("confidence", 0) / 100,
                verified=d.get("verification", {}).get("status") == "valid",
                job_title=d.get("position"),
                linkedin_url=d.get("linkedin"),
                raw=d,
            )
    except Exception as e:
        logger.warning(f"[Hunter] {e}")
    return ProviderResult(provider="hunter")


async def hunter_domain_search(domain: str, api_key: str, limit: int = 10) -> list[ProviderResult]:
    """Hunter.io — Domain Search : tous les emails connus d'un domaine."""
    url = "https://api.hunter.io/v2/domain-search"
    params = {"domain": domain, "api_key": api_key, "limit": limit}
    results = []
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, params=params)
            data = resp.json()

        for contact in data.get("data", {}).get("emails", []):
            results.append(ProviderResult(
                provider="hunter",
                email=contact.get("value"),
                first_name=contact.get("first_name"),
                last_name=contact.get("last_name"),
                job_title=contact.get("position"),
                confidence=contact.get("confidence", 0) / 100,
                verified=contact.get("verification", {}).get("status") == "valid",
                linkedin_url=contact.get("linkedin"),
                raw=contact,
            ))
    except Exception as e:
        logger.warning(f"[Hunter Domain] {e}")
    return results


# =============================================================================
# DROPCONTACT (France, RGPD-compliant)
# =============================================================================

async def dropcontact_enrich(
    first_name: str,
    last_name: str,
    company_name: str,
    website: str | None,
    api_key: str,
) -> ProviderResult:
    """
    Dropcontact — Enrichissement RGPD-compliant, spécialisé France.
    Retourne email, téléphone, poste. ~0.02€/contact.
    """
    url = "https://api.dropcontact.io/b2b/v1/enrich/async"
    payload = {
        "data": [{
            "first_name": first_name,
            "last_name": last_name,
            "company": company_name,
            "website": website or "",
        }],
        "siren": True,
        "language": "fr",
    }
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            # Soumission
            resp = await client.post(
                url,
                json=payload,
                headers={"X-Access-Token": api_key, "Content-Type": "application/json"},
            )
            data = resp.json()
            request_id = data.get("request_id")
            if not request_id:
                return ProviderResult(provider="dropcontact")

            # Polling (Dropcontact est asynchrone)
            poll_url = f"https://api.dropcontact.io/b2b/v1/enrich/async/{request_id}"
            for _ in range(10):
                await asyncio.sleep(2)
                poll = await client.get(poll_url, headers={"X-Access-Token": api_key})
                poll_data = poll.json()
                if poll_data.get("success"):
                    contacts = poll_data.get("data", [{}])
                    if contacts:
                        c = contacts[0]
                        return ProviderResult(
                            provider="dropcontact",
                            email=c.get("email", [{}])[0].get("email") if c.get("email") else None,
                            phone=c.get("phone"),
                            first_name=c.get("first_name"),
                            last_name=c.get("last_name"),
                            job_title=c.get("job"),
                            linkedin_url=c.get("linkedin"),
                            confidence=0.85,
                            verified=True,
                            raw=c,
                        )
    except Exception as e:
        logger.warning(f"[Dropcontact] {e}")
    return ProviderResult(provider="dropcontact")


# =============================================================================
# APOLLO.IO
# =============================================================================

async def apollo_people_search(
    company_name: str,
    domain: str | None,
    titles: list[str] | None = None,
    api_key: str = "",
    limit: int = 5,
) -> list[ProviderResult]:
    """
    Apollo.io — Recherche de personnes dans une entreprise.
    200 requêtes/mois sur le plan gratuit.
    """
    url = "https://api.apollo.io/v1/mixed_people/search"
    payload = {
        "api_key": api_key,
        "q_organization_name": company_name,
        "page": 1,
        "per_page": limit,
    }
    if domain:
        payload["q_organization_domains[]"] = [domain]
    if titles:
        payload["person_titles[]"] = titles

    results = []
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(url, json=payload)
            data = resp.json()

        for person in data.get("people", []):
            results.append(ProviderResult(
                provider="apollo",
                email=person.get("email"),
                first_name=person.get("first_name"),
                last_name=person.get("last_name"),
                job_title=person.get("title"),
                linkedin_url=person.get("linkedin_url"),
                phone=person.get("phone_numbers", [{}])[0].get("sanitized_number") if person.get("phone_numbers") else None,
                confidence=0.80,
                verified=person.get("email_status") == "verified",
                raw=person,
            ))
    except Exception as e:
        logger.warning(f"[Apollo] {e}")
    return results


# =============================================================================
# SNOV.IO
# =============================================================================

async def snovio_find_email(
    first_name: str,
    last_name: str,
    domain: str,
    client_id: str,
    client_secret: str,
) -> ProviderResult:
    """Snov.io — Email Finder. 150 req/mois gratuit."""
    # Auth
    token_url = "https://api.snov.io/v1/oauth/access_token"
    token_resp = None
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            token_resp = await client.post(token_url, data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
            })
            token = token_resp.json().get("access_token")
            if not token:
                return ProviderResult(provider="snovio")

            # Find email
            resp = await client.post(
                "https://api.snov.io/v1/get-emails-from-names",
                data={
                    "access_token": token,
                    "first_name": first_name,
                    "last_name": last_name,
                    "domain": domain,
                }
            )
            data = resp.json()
            emails = data.get("data", {}).get("emails", [])
            if emails:
                best = emails[0]
                return ProviderResult(
                    provider="snovio",
                    email=best.get("email"),
                    confidence=best.get("confidence", 0) / 100,
                    verified=best.get("status") == "verified",
                    raw=best,
                )
    except Exception as e:
        logger.warning(f"[Snov.io] {e}")
    return ProviderResult(provider="snovio")


# =============================================================================
# DATAGMA (spécialisé numéros mobiles France)
# =============================================================================

async def datagma_find_phone(
    linkedin_url: str,
    api_key: str,
) -> ProviderResult:
    """Datagma — Numéro mobile depuis profil LinkedIn. ~$0.10/numéro."""
    if not linkedin_url:
        return ProviderResult(provider="datagma")
    try:
        url = "https://gateway.datagma.net/api/ingress/v2/find"
        params = {"apiId": api_key, "data": linkedin_url}
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, params=params)
            data = resp.json()

        person = data.get("person", {})
        phones = person.get("phones", [])
        return ProviderResult(
            provider="datagma",
            mobile=phones[0].get("number") if phones else None,
            email=person.get("email"),
            job_title=person.get("title"),
            confidence=0.85 if phones else 0.0,
            raw=person,
        )
    except Exception as e:
        logger.warning(f"[Datagma] {e}")
    return ProviderResult(provider="datagma")
