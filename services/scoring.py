"""
Service de scoring automatique des prospects.

Score de 0 à 100 basé sur :
- Présence web (site, email, téléphone)
- Taille entreprise (tranche effectifs)
- Ancienneté (date de création)
- Avis Google (note + nombre)
- Signaux BODACC (pas de procédure collective)
- Activité commerciale (dernière interaction)
- Complétude des données

Catégories :
    HOT  : score >= 70
    WARM : score >= 40
    COLD : score < 40
"""
from __future__ import annotations

import math
from datetime import date, datetime, timezone
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from models.database.prospect import Prospect


EMPLOYEE_RANGE_SCORES: dict[str, int] = {
    "0 salarié": 2,
    "1 ou 2 salariés": 4,
    "3 à 5 salariés": 7,
    "6 à 9 salariés": 10,
    "10 à 19 salariés": 18,
    "20 à 49 salariés": 22,
    "50 à 99 salariés": 18,
    "100 à 199 salariés": 14,
    "200 à 249 salariés": 10,
    "250 à 499 salariés": 6,
    "500 à 999 salariés": 4,
    "1 000 salariés et plus": 2,
}

# Cibles idéales : PME 10-99 salariés
IDEAL_RANGES = {"10 à 19 salariés", "20 à 49 salariés", "50 à 99 salariés"}


def compute_score(prospect: "Prospect") -> tuple[float, str, dict[str, Any]]:
    """
    Calcule le score de propension d'un prospect.

    Returns:
        (score_float, category, details_dict)
    """
    details: dict[str, Any] = {}
    total = 0.0

    # ── 1. Présence digitale (25 pts max) ─────────────────────────────────
    web_score = 0
    if prospect.website:
        web_score += 12
    if prospect.email:
        web_score += 7
    if prospect.phone:
        web_score += 6
    details["web_presence"] = web_score
    total += web_score

    # ── 2. Taille entreprise (22 pts max) ─────────────────────────────────
    emp_score = 0
    if prospect.employee_range:
        emp_score = EMPLOYEE_RANGE_SCORES.get(prospect.employee_range, 5)
    details["employee_range"] = emp_score
    total += emp_score

    # ── 3. Avis Google (15 pts max) ───────────────────────────────────────
    enrichment = prospect.enrichment or {}
    rating = enrichment.get("rating")
    reviews = enrichment.get("reviews_count", 0) or 0
    google_score = 0
    if rating is not None:
        # Note sur 5 → score sur 10
        google_score += min(10, round((rating / 5) * 10))
        # Volume d'avis → bonus
        if reviews >= 50:
            google_score += 5
        elif reviews >= 20:
            google_score += 3
        elif reviews >= 5:
            google_score += 1
    details["google_rating"] = google_score
    total += google_score

    # ── 4. Ancienneté entreprise (15 pts max) ─────────────────────────────
    age_score = 0
    if prospect.creation_date:
        creation = prospect.creation_date
        if isinstance(creation, str):
            try:
                creation = date.fromisoformat(creation[:10])
            except ValueError:
                creation = None
        if creation:
            age_years = (date.today() - creation).days / 365.25
            if 2 <= age_years <= 20:
                age_score = 15
            elif age_years < 2:
                age_score = 5   # trop jeune, risqué
            else:
                age_score = 10  # très établi mais potentiellement figé
    details["company_age"] = age_score
    total += age_score

    # ── 5. Signaux BODACC (13 pts max) ────────────────────────────────────
    bodacc_score = 13  # par défaut positif (pas d'annonce = bonne santé)
    bodacc = enrichment.get("bodacc_signals", {}) or {}
    if bodacc.get("has_collective_procedure"):
        bodacc_score = 0   # procédure collective = éliminatoire
    elif bodacc.get("annonces_count", 0) > 5:
        bodacc_score = 8   # beaucoup d'annonces = activité intense (±)
    details["bodacc_signals"] = bodacc_score
    total += bodacc_score

    # ── 6. Complétude des données (10 pts max) ────────────────────────────
    fields_filled = sum([
        bool(prospect.company_name),
        bool(prospect.siren),
        bool(prospect.address),
        bool(prospect.city),
        bool(prospect.naf_code),
        bool(prospect.legal_form),
        bool(prospect.creation_date),
        bool(prospect.employee_range),
        bool(prospect.website),
        bool(prospect.phone),
    ])
    completeness_score = round((fields_filled / 10) * 10)
    details["completeness"] = completeness_score
    total += completeness_score

    # ── Clamp score 0-100 ─────────────────────────────────────────────────
    score = min(100.0, max(0.0, round(total, 1)))

    # ── Catégorie ─────────────────────────────────────────────────────────
    if score >= 70:
        category = "HOT"
    elif score >= 40:
        category = "WARM"
    else:
        category = "COLD"

    details["total"] = score
    details["category"] = category

    return score, category, details


async def score_prospect(prospect: "Prospect") -> "Prospect":
    """Met à jour le score d'un prospect et retourne le prospect modifié."""
    score, category, details = compute_score(prospect)
    prospect.propensity_score = score
    prospect.propensity_category = category
    prospect.scoring_details = details
    return prospect
