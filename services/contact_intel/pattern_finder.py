"""
Pattern Email Finder — Génère et vérifie les emails probables.

Stratégie Apollo-style sans API payante :
1. Détermine le domaine de l'entreprise (depuis website)
2. Génère tous les patterns possibles pour le contact
3. Vérifie chaque email via SMTP handshake
4. Retourne le ou les emails valides

Patterns testés (par ordre de fréquence réelle) :
    prenom.nom@domaine.com          (le plus courant : 34%)
    p.nom@domaine.com               (24%)
    prenom@domaine.com              (18%)
    nom@domaine.com                 (8%)
    prenomnom@domaine.com           (6%)
    pnom@domaine.com                (4%)
    prenom-nom@domaine.com          (3%)
    autres...                       (3%)
"""
from __future__ import annotations

import asyncio
import re
import socket
from dataclasses import dataclass
from typing import Any

from loguru import logger
from unidecode import unidecode


@dataclass
class EmailResult:
    email: str
    confidence: float   # 0.0 à 1.0
    source: str         # "smtp_verified" | "pattern" | "api_xxx"
    verified: bool      # True = SMTP validé
    pattern: str        # "firstname.lastname" etc.


def normalize_name(name: str) -> str:
    """Normalise un prénom/nom : accents, tirets, espaces."""
    if not name:
        return ""
    name = unidecode(name.strip().lower())
    name = re.sub(r"[^a-z0-9]", "", name)
    return name


def extract_domain(website: str | None) -> str | None:
    """Extrait le domaine depuis une URL de site web."""
    if not website:
        return None
    website = website.strip().lower()
    website = re.sub(r"^https?://", "", website)
    website = re.sub(r"^www\.", "", website)
    website = website.split("/")[0].strip()
    if "." not in website or len(website) < 4:
        return None
    return website


def generate_patterns(
    first_name: str,
    last_name: str,
    domain: str,
) -> list[tuple[str, str, float]]:
    """
    Génère tous les patterns d'email possibles.
    Retourne : [(email, pattern_name, confidence_prior)]
    """
    f = normalize_name(first_name)
    l = normalize_name(last_name)
    f1 = f[:1] if f else ""
    l1 = l[:1] if l else ""

    if not domain or (not f and not l):
        return []

    patterns: list[tuple[str, str, float]] = []

    if f and l:
        patterns += [
            (f"{f}.{l}@{domain}",   "firstname.lastname",  0.34),
            (f"{f1}.{l}@{domain}",  "f.lastname",          0.24),
            (f"{f}@{domain}",       "firstname",           0.18),
            (f"{l}@{domain}",       "lastname",            0.08),
            (f"{f}{l}@{domain}",    "firstnamelastname",   0.06),
            (f"{f1}{l}@{domain}",   "flastname",           0.04),
            (f"{f}-{l}@{domain}",   "firstname-lastname",  0.03),
            (f"{l}.{f}@{domain}",   "lastname.firstname",  0.02),
            (f"{f}_{l}@{domain}",   "firstname_lastname",  0.01),
        ]
    elif f:
        patterns = [(f"{f}@{domain}", "firstname", 0.5)]
    elif l:
        patterns = [(f"{l}@{domain}", "lastname", 0.5)]

    return [(e, p, c) for e, p, c in patterns if e and "@" in e and "." in e.split("@")[1]]


async def verify_email_smtp(email: str, timeout: float = 5.0) -> bool:
    """
    Vérifie un email via handshake SMTP (sans envoyer d'email).

    Protocole :
    1. Résolution MX du domaine
    2. Connexion TCP port 25
    3. EHLO → MAIL FROM → RCPT TO
    4. Si RCPT TO retourne 2xx → email valide

    Limites :
    - Certains serveurs bloquent le "catch-all" (retournent toujours 250)
    - Gmail, Microsoft bloquent RCPT TO depuis les IPs résidentielles
    - Les serveurs avec greylisting peuvent retourner 4xx temporairement
    """
    try:
        domain = email.split("@")[1]
    except IndexError:
        return False

    # 1. Résolution MX
    try:
        import dns.resolver
        mx_records = dns.resolver.resolve(domain, "MX")
        mx_host = str(sorted(mx_records, key=lambda r: r.preference)[0].exchange).rstrip(".")
    except Exception:
        # Si pas de DNS, on essaie le domaine directement
        mx_host = domain

    # 2. SMTP handshake
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(mx_host, 25),
            timeout=timeout,
        )

        async def recv():
            return (await asyncio.wait_for(reader.readline(), timeout=timeout)).decode(errors="ignore")

        async def send(cmd: str):
            writer.write((cmd + "\r\n").encode())
            await writer.drain()
            return await recv()

        # Banner
        banner = await recv()
        if not banner.startswith("2"):
            writer.close()
            return False

        # EHLO
        resp = await send("EHLO verify.b2bprospector.fr")
        if not resp.startswith("2"):
            # Essai HELO
            resp = await send("HELO verify.b2bprospector.fr")

        # MAIL FROM
        resp = await send("MAIL FROM:<verify@b2bprospector.fr>")
        if not resp.startswith("2"):
            writer.close()
            return False

        # RCPT TO — c'est ici qu'on sait si l'email existe
        resp = await send(f"RCPT TO:<{email}>")
        writer.close()

        # 250/251 = valide, 550/551/553 = invalide, 4xx = temporaire
        if resp.startswith("2"):
            return True
        return False

    except Exception as e:
        logger.debug(f"[SMTP] {email}: {e}")
        return False


async def find_emails_by_pattern(
    first_name: str,
    last_name: str,
    domain: str,
    max_verify: int = 5,
    smtp_timeout: float = 4.0,
) -> list[EmailResult]:
    """
    Trouve les emails probables via patterns + vérification SMTP.

    Args:
        first_name: Prénom du contact
        last_name:  Nom du contact
        domain:     Domaine de l'entreprise (ex: "acme.fr")
        max_verify: Nombre max de patterns à vérifier par SMTP
        smtp_timeout: Timeout SMTP en secondes

    Returns:
        Liste d'EmailResult triée par confiance décroissante
    """
    patterns = generate_patterns(first_name, last_name, domain)
    if not patterns:
        return []

    results: list[EmailResult] = []

    # Vérifie les N patterns les plus probables
    tasks = [
        verify_email_smtp(email, smtp_timeout)
        for email, _, _ in patterns[:max_verify]
    ]

    try:
        verifications = await asyncio.gather(*tasks, return_exceptions=True)
    except Exception:
        verifications = [False] * len(tasks)

    for (email, pattern, prior_conf), verified in zip(patterns[:max_verify], verifications):
        is_verified = isinstance(verified, bool) and verified
        confidence = 0.95 if is_verified else prior_conf
        results.append(EmailResult(
            email=email,
            confidence=confidence,
            source="smtp_verified" if is_verified else "pattern",
            verified=is_verified,
            pattern=pattern,
        ))

    # Ajoute les patterns non vérifiés (avec confiance réduite)
    verified_emails = {r.email for r in results}
    for email, pattern, conf in patterns[max_verify:]:
        if email not in verified_emails:
            results.append(EmailResult(
                email=email,
                confidence=conf * 0.5,
                source="pattern",
                verified=False,
                pattern=pattern,
            ))

    # Tri : vérifiés en premier, puis par confiance
    results.sort(key=lambda r: (r.verified, r.confidence), reverse=True)
    return results
