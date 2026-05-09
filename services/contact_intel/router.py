"""
ContactIntelRouter — Orchestrateur Apollo-style.

Waterfall de sources :
    Gratuit (toujours actif) :
        1. Website Extractor    → emails depuis le site web
        2. Pattern Finder       → génération + vérification SMTP
        3. AI Contact Finder    → Claude recherche le contact

    Payant (si clé API configurée) :
        4. Hunter.io            → HUNTER_API_KEY
        5. Dropcontact          → DROPCONTACT_API_KEY
        6. Apollo.io            → APOLLO_API_KEY
        7. Snov.io              → SNOVIO_CLIENT_ID + SNOVIO_CLIENT_SECRET
        8. Datagma              → DATAGMA_API_KEY (mobile uniquement)

S'arrête dès qu'un email vérifié est trouvé.
Si aucune source ne trouve, retourne les patterns non vérifiés.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from loguru import logger

from core.config import settings
from services.contact_intel.api_providers import (
    ProviderResult,
    apollo_people_search,
    datagma_find_phone,
    dropcontact_enrich,
    hunter_domain_search,
    hunter_find_email,
    snovio_find_email,
)
from services.contact_intel.pattern_finder import (
    extract_domain,
    find_emails_by_pattern,
)
from services.contact_intel.website_extractor import extract_from_website


@dataclass
class ContactIntelResult:
    """Résultat consolidé d'une recherche de contact."""
    prospect_id: str | None = None
    company_name: str | None = None
    domain: str | None = None

    # Contact trouvé
    first_name: str | None = None
    last_name: str | None = None
    job_title: str | None = None
    email: str | None = None
    email_confidence: float = 0.0
    email_verified: bool = False
    phone: str | None = None
    mobile: str | None = None
    linkedin_url: str | None = None

    # Données du site web
    all_emails: list[str] = field(default_factory=list)
    all_phones: list[str] = field(default_factory=list)
    linkedin_company: str | None = None

    # Méta
    sources_used: list[str] = field(default_factory=list)
    providers_tried: list[str] = field(default_factory=list)
    enriched_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "prospect_id": self.prospect_id,
            "company_name": self.company_name,
            "domain": self.domain,
            "contact": {
                "first_name": self.first_name,
                "last_name": self.last_name,
                "job_title": self.job_title,
                "email": self.email,
                "email_confidence": round(self.email_confidence, 2),
                "email_verified": self.email_verified,
                "phone": self.phone,
                "mobile": self.mobile,
                "linkedin_url": self.linkedin_url,
            },
            "company_data": {
                "all_emails": self.all_emails,
                "all_phones": self.all_phones,
                "linkedin_company": self.linkedin_company,
            },
            "meta": {
                "sources_used": self.sources_used,
                "providers_tried": self.providers_tried,
                "enriched_at": self.enriched_at,
            },
        }


async def find_contact(
    company_name: str,
    website: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
    job_title: str | None = None,
    prospect_id: str | None = None,
    stop_on_verified: bool = True,
) -> ContactIntelResult:
    """
    Lance la recherche de contact en cascade (waterfall Apollo-style).

    Args:
        company_name:      Nom de l'entreprise
        website:           URL du site web (pour extraction + domaine)
        first_name:        Prénom du contact (si connu)
        last_name:         Nom du contact (si connu)
        job_title:         Poste recherché (ex: "Dirigeant", "DG", "CEO")
        prospect_id:       ID du prospect B2B Prospector
        stop_on_verified:  Arrête dès qu'un email SMTP-vérifié est trouvé

    Returns:
        ContactIntelResult consolidé
    """
    result = ContactIntelResult(
        prospect_id=prospect_id,
        company_name=company_name,
        enriched_at=str(date.today()),
    )

    domain = extract_domain(website)
    result.domain = domain

    # =========================================================================
    # ÉTAPE 1 — Extraction site web (gratuit)
    # =========================================================================
    if website:
        logger.info(f"[ContactIntel] Scan site web : {website}")
        web_data = await extract_from_website(website, domain)
        result.all_emails = web_data.get("emails", [])
        result.all_phones = web_data.get("phones", [])
        result.linkedin_company = web_data.get("linkedin_company")
        if web_data.get("emails"):
            result.sources_used.append("website_extractor")

        # Si email direct trouvé et pas de contact spécifique recherché
        if result.all_emails and not first_name and not last_name:
            result.email = result.all_emails[0]
            result.email_confidence = 0.7
            if not stop_on_verified:
                pass  # continue pour enrichir

    # =========================================================================
    # ÉTAPE 2 — Pattern Finder + SMTP (gratuit)
    # =========================================================================
    if domain and first_name and last_name:
        logger.info(f"[ContactIntel] Pattern finder : {first_name} {last_name} @ {domain}")
        result.providers_tried.append("pattern_finder")
        patterns = await find_emails_by_pattern(first_name, last_name, domain)
        if patterns:
            result.sources_used.append("pattern_finder")
            best = patterns[0]
            if best.verified or not result.email:
                result.email = best.email
                result.email_confidence = best.confidence
                result.email_verified = best.verified
            if stop_on_verified and best.verified:
                logger.success(f"[ContactIntel] Email SMTP vérifié : {best.email}")
                return _finalize(result, first_name, last_name, job_title)

    # =========================================================================
    # ÉTAPE 3 — Hunter.io (si clé configurée)
    # =========================================================================
    hunter_key = getattr(settings, "HUNTER_API_KEY", "")
    if hunter_key and domain:
        result.providers_tried.append("hunter")
        if first_name and last_name:
            h = await hunter_find_email(first_name, last_name, domain, hunter_key)
            if h.email:
                result.sources_used.append("hunter")
                result.email = h.email
                result.email_confidence = h.confidence
                result.email_verified = h.verified
                result.linkedin_url = result.linkedin_url or h.linkedin_url
                if stop_on_verified and h.verified:
                    return _finalize(result, first_name, last_name, job_title or h.job_title)
        else:
            # Domain search : tous les contacts connus
            contacts = await hunter_domain_search(domain, hunter_key, limit=5)
            if contacts:
                result.sources_used.append("hunter")
                result.all_emails += [c.email for c in contacts if c.email]
                if not result.email and contacts[0].email:
                    best_contact = contacts[0]
                    result.email = best_contact.email
                    result.email_confidence = best_contact.confidence
                    result.first_name = result.first_name or best_contact.first_name
                    result.last_name = result.last_name or best_contact.last_name
                    result.job_title = result.job_title or best_contact.job_title

    # =========================================================================
    # ÉTAPE 4 — Dropcontact (si clé configurée)
    # =========================================================================
    dropcontact_key = getattr(settings, "DROPCONTACT_API_KEY", "")
    if dropcontact_key and first_name and last_name:
        result.providers_tried.append("dropcontact")
        dc = await dropcontact_enrich(first_name, last_name, company_name, website, dropcontact_key)
        if dc.email:
            result.sources_used.append("dropcontact")
            result.email = dc.email
            result.email_confidence = dc.confidence
            result.email_verified = dc.verified
            result.phone = result.phone or dc.phone
            result.linkedin_url = result.linkedin_url or dc.linkedin_url
            if stop_on_verified:
                return _finalize(result, first_name, last_name, job_title or dc.job_title)

    # =========================================================================
    # ÉTAPE 5 — Apollo.io (si clé configurée)
    # =========================================================================
    apollo_key = getattr(settings, "APOLLO_API_KEY", "")
    if apollo_key:
        result.providers_tried.append("apollo")
        titles = [job_title] if job_title else ["Directeur", "CEO", "Gérant", "DG", "Founder"]
        contacts = await apollo_people_search(company_name, domain, titles, apollo_key, limit=3)
        if contacts:
            result.sources_used.append("apollo")
            best = contacts[0]
            if not result.email or best.verified:
                result.email = best.email
                result.email_confidence = best.confidence
                result.email_verified = best.verified
            result.phone = result.phone or best.phone
            result.linkedin_url = result.linkedin_url or best.linkedin_url
            result.first_name = result.first_name or best.first_name
            result.last_name = result.last_name or best.last_name
            result.job_title = result.job_title or best.job_title

    # =========================================================================
    # ÉTAPE 6 — Snov.io (si clé configurée)
    # =========================================================================
    snovio_id = getattr(settings, "SNOVIO_CLIENT_ID", "")
    snovio_secret = getattr(settings, "SNOVIO_CLIENT_SECRET", "")
    if snovio_id and snovio_secret and first_name and last_name and domain:
        result.providers_tried.append("snovio")
        sn = await snovio_find_email(first_name, last_name, domain, snovio_id, snovio_secret)
        if sn.email and not result.email_verified:
            result.sources_used.append("snovio")
            result.email = sn.email
            result.email_confidence = sn.confidence
            result.email_verified = sn.verified

    # =========================================================================
    # ÉTAPE 7 — Datagma mobile (si clé + LinkedIn URL)
    # =========================================================================
    datagma_key = getattr(settings, "DATAGMA_API_KEY", "")
    if datagma_key and result.linkedin_url and not result.mobile:
        result.providers_tried.append("datagma")
        dg = await datagma_find_phone(result.linkedin_url, datagma_key)
        if dg.mobile:
            result.sources_used.append("datagma")
            result.mobile = dg.mobile

    return _finalize(result, first_name, last_name, job_title)


def _finalize(
    result: ContactIntelResult,
    first_name: str | None,
    last_name: str | None,
    job_title: str | None,
) -> ContactIntelResult:
    result.first_name = result.first_name or first_name
    result.last_name = result.last_name or last_name
    result.job_title = result.job_title or job_title
    # Déduplique
    result.all_emails = list(dict.fromkeys(e for e in result.all_emails if e))
    result.all_phones = list(dict.fromkeys(p for p in result.all_phones if p))
    return result
