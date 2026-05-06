"""
Script de seed — Données de démo + admin par défaut.

Usage :
    python -m scripts.seed

À exécuter UNE FOIS après les migrations.
Si déjà exécuté, ne fait rien (idempotent).
"""
import asyncio
import os
import sys
from pathlib import Path

# Ajout du root au PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datetime import date  # noqa: E402

from loguru import logger  # noqa: E402
from sqlalchemy import select  # noqa: E402

from core.database import AsyncSessionLocal, close_db  # noqa: E402
from core.security import hash_password  # noqa: E402
from models.database.pipeline_stage import PipelineStage  # noqa: E402
from models.database.plugin_state import PluginState  # noqa: E402
from models.database.prospect import Contact, Prospect  # noqa: E402
from models.database.user import User  # noqa: E402

# =============================================================================
# DEFAULT DATA
# =============================================================================

DEFAULT_STAGES = [
    {"name": "Nouveau", "slug": "nouveau", "color": "#3b82f6", "order": 1, "description": "Prospect non encore contacté"},
    {"name": "Contacté", "slug": "contacte", "color": "#eab308", "order": 2, "description": "Premier contact effectué"},
    {"name": "RDV pris", "slug": "rdv-pris", "color": "#f97316", "order": 3, "description": "Rendez-vous planifié"},
    {"name": "En négociation", "slug": "negociation", "color": "#a855f7", "order": 4, "description": "Discussion commerciale active"},
    {"name": "Gagné", "slug": "gagne", "color": "#22c55e", "order": 5, "is_won": True, "description": "Affaire conclue"},
    {"name": "Perdu", "slug": "perdu", "color": "#ef4444", "order": 6, "is_lost": True, "description": "Prospect perdu"},
]

DEFAULT_PLUGINS = [
    {"name": "prospects", "version": "1.1.0", "description": "Gestion CRUD des prospects + ajout par SIRET + import CSV/XLSX", "is_active": True},
    {"name": "pipeline", "version": "1.1.0", "description": "Pipeline Kanban — étapes commerciales et drag-n-drop", "is_active": True},
    {"name": "dashboard", "version": "1.1.0", "description": "Agrégats KPI pour le dashboard principal", "is_active": True},
    {"name": "system", "version": "1.1.0", "description": "Endpoints système — santé, info, plugins state", "is_active": True},
    {"name": "scraper_insee", "version": "1.0.0", "description": "Scraper INSEE/Sirene (API publique data.gouv.fr)", "is_active": True},
    {"name": "scraper_bodacc", "version": "1.0.0", "description": "Scraper BODACC (API publique data.gouv.fr)", "is_active": True},
    {"name": "scraper_pappers", "version": "1.0.0", "description": "Scraper Pappers (HTML public)", "is_active": True},
    {"name": "scraper_pages_jaunes", "version": "1.0.0", "description": "Scraper Pages Jaunes", "is_active": True},
    {"name": "scraper_google_maps", "version": "1.0.0", "description": "Scraper Google Maps (Playwright)", "is_active": True},
    {"name": "semantic_analyzer", "version": "1.0.0", "description": "Analyse NLP douleurs/valeurs (Phase 3)", "is_active": False},
    {"name": "predictive_scorer", "version": "1.0.0", "description": "Scoring HOT/WARM/COLD (Phase 3)", "is_active": False},
    {"name": "automation_engine", "version": "1.0.0", "description": "Séquences automatisées email/LinkedIn (Phase 3)", "is_active": False},
    {"name": "compliance_guard", "version": "1.0.0", "description": "RGPD + fraude + solvabilité (Phase 3)", "is_active": False},
]

DEMO_PROSPECTS = [
    {
        "company_name": "Boulangerie Martin",
        "siren": "751234567",
        "naf_code": "10.71B",
        "naf_label": "Cuisson de produits de boulangerie",
        "city": "Roubaix",
        "postal_code": "59100",
        "department": "59",
        "region": "Hauts-de-France",
        "phone": "03 20 00 00 01",
        "email": "contact@boulangerie-martin.fr",
        "website": "https://boulangerie-martin.fr",
        "estimated_revenue": 12000.0,
        "stage_slug": "nouveau",
        "tags": ["restauration", "local"],
        "directors": [("Pierre", "Martin", "Gérant")],
    },
    {
        "company_name": "TechWeb Solutions",
        "siren": "812345678",
        "naf_code": "62.01Z",
        "naf_label": "Programmation informatique",
        "city": "Lille",
        "postal_code": "59000",
        "department": "59",
        "region": "Hauts-de-France",
        "phone": "03 20 00 00 02",
        "email": "hello@techweb.fr",
        "website": "https://techweb.fr",
        "estimated_revenue": 25000.0,
        "stage_slug": "contacte",
        "propensity_score": 78.0,
        "propensity_category": "HOT",
        "tags": ["IT", "scale-up"],
        "directors": [("Sophie", "Dupont", "CEO"), ("Marc", "Lefèvre", "CTO")],
    },
    {
        "company_name": "Garage Dubois",
        "siren": "523456789",
        "naf_code": "45.20A",
        "naf_label": "Entretien et réparation de véhicules",
        "city": "Tourcoing",
        "postal_code": "59200",
        "department": "59",
        "region": "Hauts-de-France",
        "phone": "03 20 00 00 03",
        "email": "garage.dubois@orange.fr",
        "website": None,
        "estimated_revenue": 8000.0,
        "stage_slug": "rdv-pris",
        "propensity_score": 55.0,
        "propensity_category": "WARM",
        "tags": ["automobile"],
        "directors": [("Jean", "Dubois", "Gérant")],
    },
    {
        "company_name": "Restaurant Le Carillon",
        "siren": "634567890",
        "naf_code": "56.10A",
        "naf_label": "Restauration traditionnelle",
        "city": "Lille",
        "postal_code": "59000",
        "department": "59",
        "region": "Hauts-de-France",
        "phone": "03 20 00 00 04",
        "email": "contact@lecarillon.fr",
        "website": "https://lecarillon-lille.fr",
        "estimated_revenue": 18000.0,
        "stage_slug": "negociation",
        "propensity_score": 82.0,
        "propensity_category": "HOT",
        "tags": ["restauration", "ville"],
        "directors": [("Élise", "Bernard", "Directrice")],
    },
    {
        "company_name": "Avocat Conseil Lefebvre",
        "siren": "745678901",
        "naf_code": "69.10Z",
        "naf_label": "Activités juridiques",
        "city": "Roubaix",
        "postal_code": "59100",
        "department": "59",
        "region": "Hauts-de-France",
        "phone": "03 20 00 00 05",
        "email": "cabinet@lefebvre-avocat.fr",
        "website": "https://lefebvre-avocat.fr",
        "estimated_revenue": 30000.0,
        "stage_slug": "gagne",
        "propensity_score": 90.0,
        "propensity_category": "HOT",
        "tags": ["B2B", "premium"],
        "directors": [("Camille", "Lefebvre", "Avocate associée")],
    },
    {
        "company_name": "Salon de coiffure Élégance",
        "siren": "856789012",
        "naf_code": "96.02A",
        "naf_label": "Coiffure",
        "city": "Wattrelos",
        "postal_code": "59150",
        "department": "59",
        "region": "Hauts-de-France",
        "phone": "03 20 00 00 06",
        "email": "elegance@hairmail.fr",
        "website": None,
        "estimated_revenue": 5000.0,
        "stage_slug": "perdu",
        "propensity_score": 25.0,
        "propensity_category": "COLD",
        "tags": ["beauté"],
        "directors": [("Aurélie", "Petit", "Gérante")],
    },
    {
        "company_name": "Plomberie Express",
        "siren": "967890123",
        "naf_code": "43.22A",
        "naf_label": "Travaux d'installation d'eau et de gaz",
        "city": "Roubaix",
        "postal_code": "59100",
        "department": "59",
        "region": "Hauts-de-France",
        "phone": "03 20 00 00 07",
        "email": "contact@plomberie-express.fr",
        "website": "https://plomberie-express.fr",
        "estimated_revenue": 15000.0,
        "stage_slug": "nouveau",
        "tags": ["BTP"],
        "directors": [("Olivier", "Moreau", "Gérant")],
    },
    {
        "company_name": "Cabinet Dentaire Saint-Michel",
        "siren": "178901234",
        "naf_code": "86.23Z",
        "naf_label": "Pratique dentaire",
        "city": "Lille",
        "postal_code": "59000",
        "department": "59",
        "region": "Hauts-de-France",
        "phone": "03 20 00 00 08",
        "email": "rdv@dentaire-saint-michel.fr",
        "website": "https://dentaire-saint-michel.fr",
        "estimated_revenue": 22000.0,
        "stage_slug": "contacte",
        "propensity_score": 68.0,
        "propensity_category": "WARM",
        "tags": ["santé", "premium"],
        "directors": [("Dr. Antoine", "Rousseau", "Praticien")],
    },
    {
        "company_name": "Fleuriste Les Quatre Saisons",
        "siren": "289012345",
        "naf_code": "47.76Z",
        "naf_label": "Commerce de détail de fleurs",
        "city": "Tourcoing",
        "postal_code": "59200",
        "department": "59",
        "region": "Hauts-de-France",
        "phone": "03 20 00 00 09",
        "email": "boutique@4saisons-fleurs.fr",
        "website": None,
        "estimated_revenue": 6500.0,
        "stage_slug": "rdv-pris",
        "propensity_score": 60.0,
        "propensity_category": "WARM",
        "tags": ["commerce"],
        "directors": [("Marie", "Garcia", "Gérante")],
    },
    {
        "company_name": "Auto-École Excellence",
        "siren": "390123456",
        "naf_code": "85.53Z",
        "naf_label": "Enseignement de la conduite",
        "city": "Roubaix",
        "postal_code": "59100",
        "department": "59",
        "region": "Hauts-de-France",
        "phone": "03 20 00 00 10",
        "email": "info@autoecole-excellence.fr",
        "website": "https://autoecole-excellence.fr",
        "estimated_revenue": 11000.0,
        "stage_slug": "negociation",
        "propensity_score": 75.0,
        "propensity_category": "HOT",
        "tags": ["formation"],
        "directors": [("Karim", "Benali", "Directeur")],
    },
]


# =============================================================================
# SEED LOGIC
# =============================================================================

async def seed_users(db) -> None:
    email = os.getenv("ADMIN_EMAIL", "admin@le-publicitaire.fr")
    password = os.getenv("ADMIN_PASSWORD", "Admin1234!")
    full_name = os.getenv("ADMIN_FULL_NAME", "Administrateur")

    existing = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if existing:
        logger.info(f"✓ User admin déjà existant : {email}")
        return

    user = User(
        email=email,
        full_name=full_name,
        hashed_password=hash_password(password),
        role="admin",
        is_active=True,
    )
    db.add(user)
    await db.commit()
    logger.success(f"✓ Admin créé : {email}")


async def seed_stages(db) -> dict[str, str]:
    stages_map: dict[str, str] = {}
    for stage_data in DEFAULT_STAGES:
        existing = (
            await db.execute(select(PipelineStage).where(PipelineStage.slug == stage_data["slug"]))
        ).scalar_one_or_none()

        if existing:
            stages_map[stage_data["slug"]] = str(existing.id)
            continue

        stage = PipelineStage(**stage_data)
        db.add(stage)
        await db.flush()
        stages_map[stage_data["slug"]] = str(stage.id)
        logger.info(f"  ✓ Étape créée : {stage_data['name']}")

    await db.commit()
    logger.success(f"✓ {len(stages_map)} étapes pipeline en base")
    return stages_map


async def seed_plugins(db) -> None:
    for plugin_data in DEFAULT_PLUGINS:
        existing = (
            await db.execute(select(PluginState).where(PluginState.name == plugin_data["name"]))
        ).scalar_one_or_none()

        if existing:
            continue

        plugin = PluginState(**plugin_data)
        db.add(plugin)

    await db.commit()
    count = (await db.execute(select(PluginState))).scalars().all()
    logger.success(f"✓ {len(count)} plugins enregistrés")


async def seed_demo_prospects(db, stages_map: dict[str, str]) -> None:
    from uuid import UUID as _UUID

    # Skip si déjà des prospects
    existing_count = len((await db.execute(select(Prospect))).scalars().all())
    if existing_count >= len(DEMO_PROSPECTS):
        logger.info(f"✓ Déjà {existing_count} prospects en base, pas de seed démo")
        return

    for p_data in DEMO_PROSPECTS:
        # Skip si SIREN déjà existant
        existing = (
            await db.execute(select(Prospect).where(Prospect.siren == p_data["siren"]))
        ).scalar_one_or_none()
        if existing:
            continue

        directors = p_data.pop("directors", [])
        stage_slug = p_data.pop("stage_slug")
        stage_id = stages_map.get(stage_slug)

        prospect = Prospect(
            **p_data,
            country="FR",
            stage_id=_UUID(stage_id) if stage_id else None,
            sources_used=["seed"],
            last_enriched_at=date.today(),
            consent_given=True,
        )

        for fname, lname, role in directors:
            prospect.contacts.append(
                Contact(
                    first_name=fname,
                    last_name=lname,
                    role=role,
                    is_primary=(directors.index((fname, lname, role)) == 0),
                )
            )

        db.add(prospect)

    await db.commit()
    logger.success(f"✓ {len(DEMO_PROSPECTS)} prospects de démo insérés")


# =============================================================================
# MAIN
# =============================================================================

async def main() -> None:
    logger.info("🌱 Démarrage du seed...")

    async with AsyncSessionLocal() as db:
        await seed_users(db)
        stages_map = await seed_stages(db)
        await seed_plugins(db)
        await seed_demo_prospects(db, stages_map)

    await close_db()
    logger.success("✅ Seed terminé !")


if __name__ == "__main__":
    asyncio.run(main())
