"""
Website Contact Extractor — Extrait emails et téléphones depuis le site web.

Pages scannées :
    / (homepage)
    /contact
    /a-propos, /about, /about-us, /equipe, /team
    /mentions-legales, /legal
    /nous-contacter, /contactez-nous

Extraction :
    - Emails via regex
    - Téléphones via regex (formats FR + international)
    - Noms depuis le DOM (sections équipe, dirigeants)
    - Réseaux sociaux (LinkedIn company page)
"""
import asyncio
import re
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx
from loguru import logger
from selectolax.parser import HTMLParser

CONTACT_PATHS = [
    "/", "/contact", "/nous-contacter", "/contactez-nous",
    "/about", "/a-propos", "/equipe", "/team",
    "/mentions-legales", "/legal", "/qui-sommes-nous",
]

EMAIL_REGEX = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
    re.IGNORECASE,
)

PHONE_REGEX = re.compile(
    r"(?:(?:\+33|0033|0)\s?[1-9](?:[\s.\-]?\d{2}){4})",
    re.IGNORECASE,
)

LINKEDIN_REGEX = re.compile(
    r"linkedin\.com/(?:company|in)/([a-zA-Z0-9\-_]+)",
    re.IGNORECASE,
)

# Emails à ignorer (exemples, placeholders, no-reply...)
EXCLUDED_EMAILS = {
    "example@", "test@", "noreply@", "no-reply@",
    "info@example", "contact@example", "@example.com",
    "email@", "votre@", "votre-email@",
}


def is_valid_email(email: str, domain: str | None = None) -> bool:
    email = email.lower()
    for excl in EXCLUDED_EMAILS:
        if excl in email:
            return False
    if len(email) > 100:
        return False
    if domain and domain.lower() not in email:
        # Accepte quand même si c'est un email valide d'un autre domaine
        pass
    return True


def normalize_phone(phone: str) -> str:
    phone = re.sub(r"[\s.\-]", "", phone)
    if phone.startswith("0033"):
        phone = "+33" + phone[4:]
    elif phone.startswith("33") and len(phone) == 11:
        phone = "+33" + phone[2:]
    elif phone.startswith("0") and len(phone) == 10:
        phone = "+33" + phone[1:]
    return phone


async def extract_from_website(
    website: str,
    domain: str | None = None,
    max_pages: int = 4,
    timeout: float = 8.0,
) -> dict[str, Any]:
    """
    Scanne un site web et extrait contacts, emails, téléphones, LinkedIn.

    Returns:
        {
            emails: list[str],
            phones: list[str],
            linkedin_company: str | None,
            pages_scanned: int,
            raw_text_contacts: list[str],  # noms trouvés dans sections équipe
        }
    """
    if not website:
        return {"emails": [], "phones": [], "linkedin_company": None, "pages_scanned": 0}

    # Normalise l'URL
    if not website.startswith(("http://", "https://")):
        website = "https://" + website
    base = website.rstrip("/")

    found_emails: set[str] = set()
    found_phones: set[str] = set()
    linkedin_company: str | None = None
    pages_scanned = 0

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; B2BProspector/1.1; contact contact@le-publicitaire.fr)",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "fr-FR,fr;q=0.9",
    }

    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, headers=headers) as client:
        for path in CONTACT_PATHS[:max_pages]:
            url = urljoin(base, path)
            try:
                resp = await client.get(url)
                if resp.status_code not in (200, 301, 302):
                    continue
                html = resp.text
                pages_scanned += 1

                # Emails
                for email in EMAIL_REGEX.findall(html):
                    email = email.lower().strip(".")
                    if is_valid_email(email, domain):
                        found_emails.add(email)

                # Téléphones
                for phone in PHONE_REGEX.findall(html):
                    normalized = normalize_phone(phone)
                    if len(normalized) >= 10:
                        found_phones.add(normalized)

                # LinkedIn
                if not linkedin_company:
                    match = LINKEDIN_REGEX.search(html)
                    if match:
                        linkedin_company = match.group(1)

                await asyncio.sleep(0.5)  # politesse

            except Exception as e:
                logger.debug(f"[WebExtract] {url}: {e}")
                continue

    # Filtre les emails génériques (garde les plus spécifiques d'abord)
    emails_sorted = sorted(
        found_emails,
        key=lambda e: (
            0 if domain and domain in e else 1,  # priorité au domaine de l'entreprise
            len(e),
        )
    )

    return {
        "emails": emails_sorted[:10],
        "phones": list(found_phones)[:5],
        "linkedin_company": linkedin_company,
        "pages_scanned": pages_scanned,
    }
