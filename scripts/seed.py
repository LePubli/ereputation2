"""
Script de seed — Données de démo complètes pour B2B Prospector.

Usage :
    python -m scripts.seed

Idempotent : peut être relancé sans casser les données existantes.
"""
import asyncio
import os
import random
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from loguru import logger  # noqa: E402
from sqlalchemy import select  # noqa: E402

from core.database import AsyncSessionLocal, close_db  # noqa: E402
from core.security import hash_password  # noqa: E402
from models.database.abm_list import ABMList  # noqa: E402
from models.database.activity import Activity  # noqa: E402
from models.database.email_sequence import EmailSequence, SequenceStep  # noqa: E402
from models.database.inbound_source import InboundSource  # noqa: E402
from models.database.pipeline_stage import PipelineStage  # noqa: E402
from models.database.plugin_state import PluginState  # noqa: E402
from models.database.prospect import Contact, Prospect  # noqa: E402
from models.database.signal import Signal  # noqa: E402
from models.database.user import User  # noqa: E402
from models.database.webhook import Webhook  # noqa: E402

# =============================================================================
# CONFIG — STAGES, PLUGINS
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
    {"name": "prospects", "version": "1.1.0", "description": "Gestion CRUD des prospects", "is_active": True},
    {"name": "pipeline", "version": "1.1.0", "description": "Pipeline Kanban — drag-n-drop", "is_active": True},
    {"name": "dashboard", "version": "1.1.0", "description": "KPI dashboard principal", "is_active": True},
    {"name": "system", "version": "1.1.0", "description": "Endpoints système", "is_active": True},
    {"name": "auth", "version": "1.0.0", "description": "Authentification JWT", "is_active": True},
    {"name": "activities", "version": "1.0.0", "description": "Activités prospects", "is_active": True},
    {"name": "agent", "version": "1.0.0", "description": "AI Agent multi-LLM", "is_active": True},
    {"name": "webhooks", "version": "1.0.0", "description": "Webhooks sortants", "is_active": True},
    {"name": "sequencer", "version": "1.0.0", "description": "Séquences email", "is_active": True},
    {"name": "signals", "version": "1.0.0", "description": "Détection de signaux business", "is_active": True},
    {"name": "inbound", "version": "1.0.0", "description": "Leads entrants via webhook", "is_active": True},
    {"name": "abm", "version": "1.0.0", "description": "Account-Based Marketing + TAM", "is_active": True},
    {"name": "crm_sync", "version": "1.0.0", "description": "Synchronisation HubSpot/SF", "is_active": True},
    {"name": "analytics", "version": "1.0.0", "description": "KPIs et exports CSV", "is_active": True},
    {"name": "sourcing", "version": "1.0.0", "description": "Jobs de scraping", "is_active": True},
    {"name": "export", "version": "1.0.0", "description": "Export Excel/CSV", "is_active": True},
    {"name": "notifications", "version": "1.0.0", "description": "WebSocket notifications", "is_active": True},
    {"name": "scraper_insee", "version": "1.0.0", "description": "Scraper INSEE/Sirene", "is_active": True},
    {"name": "scraper_bodacc", "version": "1.0.0", "description": "Scraper BODACC", "is_active": True},
    {"name": "scraper_pappers", "version": "1.0.0", "description": "Scraper Pappers", "is_active": True},
    {"name": "scraper_pages_jaunes", "version": "1.0.0", "description": "Scraper Pages Jaunes", "is_active": True},
    {"name": "scraper_google_maps", "version": "1.0.0", "description": "Scraper Google Maps", "is_active": False},
    {"name": "scraper_societe", "version": "1.0.0", "description": "Scraper Societe.com", "is_active": True},
    {"name": "scraper_trustpilot", "version": "1.0.0", "description": "Scraper Trustpilot", "is_active": True},
]

# =============================================================================
# PROSPECTS DE DEMO
# =============================================================================

DEMO_PROSPECTS = [
    {"company_name": "Boulangerie Martin", "siren": "751234567", "naf_code": "10.71B", "naf_label": "Cuisson de produits de boulangerie", "city": "Roubaix", "postal_code": "59100", "department": "59", "region": "Hauts-de-France", "phone": "03 20 00 00 01", "email": "contact@boulangerie-martin.fr", "website": "https://boulangerie-martin.fr", "estimated_revenue": 12000.0, "stage_slug": "nouveau", "tags": ["restauration", "local"], "directors": [("Pierre", "Martin", "Gérant")], "employee_range": "3-5"},
    {"company_name": "TechWeb Solutions", "siren": "812345678", "naf_code": "62.01Z", "naf_label": "Programmation informatique", "city": "Lille", "postal_code": "59000", "department": "59", "region": "Hauts-de-France", "phone": "03 20 00 00 02", "email": "hello@techweb.fr", "website": "https://techweb.fr", "estimated_revenue": 25000.0, "stage_slug": "contacte", "propensity_score": 78.0, "propensity_category": "HOT", "tags": ["IT", "scale-up"], "directors": [("Sophie", "Dupont", "CEO"), ("Marc", "Lefèvre", "CTO")], "employee_range": "20-49"},
    {"company_name": "Garage Dubois", "siren": "523456789", "naf_code": "45.20A", "naf_label": "Entretien et réparation de véhicules", "city": "Tourcoing", "postal_code": "59200", "department": "59", "region": "Hauts-de-France", "phone": "03 20 00 00 03", "email": "garage.dubois@orange.fr", "estimated_revenue": 8000.0, "stage_slug": "rdv-pris", "propensity_score": 62.0, "propensity_category": "WARM", "tags": ["automotive"], "directors": [("Jean", "Dubois", "Gérant")], "employee_range": "6-9"},
    {"company_name": "Restaurant Le Carillon", "siren": "434567890", "naf_code": "56.10A", "naf_label": "Restauration traditionnelle", "city": "Lille", "postal_code": "59000", "department": "59", "region": "Hauts-de-France", "phone": "03 20 00 00 04", "email": "contact@carillon-lille.fr", "website": "https://carillon-lille.fr", "estimated_revenue": 18000.0, "stage_slug": "negociation", "propensity_score": 85.0, "propensity_category": "HOT", "tags": ["restauration", "premium"], "directors": [("Élodie", "Bernard", "Gérante")], "employee_range": "10-19"},
    {"company_name": "Avocat Conseil Lefebvre", "siren": "345678901", "naf_code": "69.10Z", "naf_label": "Activités juridiques", "city": "Lille", "postal_code": "59000", "department": "59", "region": "Hauts-de-France", "phone": "03 20 00 00 05", "email": "cabinet@lefebvre-avocat.fr", "website": "https://lefebvre-avocat.fr", "estimated_revenue": 35000.0, "stage_slug": "gagne", "propensity_score": 90.0, "propensity_category": "HOT", "tags": ["juridique", "B2B"], "directors": [("Catherine", "Lefebvre", "Avocate associée")], "employee_range": "6-9"},
    {"company_name": "Salon de coiffure Élégance", "siren": "256789012", "naf_code": "96.02A", "naf_label": "Coiffure", "city": "Roubaix", "postal_code": "59100", "department": "59", "region": "Hauts-de-France", "phone": "03 20 00 00 06", "email": "elegance.coiffure@gmail.com", "estimated_revenue": 6000.0, "stage_slug": "perdu", "propensity_score": 30.0, "propensity_category": "COLD", "tags": ["beauté"], "directors": [("Nadia", "Rahmani", "Gérante")], "employee_range": "1-2"},
    {"company_name": "Plomberie Express", "siren": "167890123", "naf_code": "43.22A", "naf_label": "Travaux d'installation d'eau et de gaz", "city": "Villeneuve-d'Ascq", "postal_code": "59650", "department": "59", "region": "Hauts-de-France", "phone": "03 20 00 00 07", "email": "contact@plomberie-express.fr", "website": "https://plomberie-express.fr", "estimated_revenue": 15000.0, "stage_slug": "nouveau", "propensity_score": 55.0, "propensity_category": "WARM", "tags": ["BTP"], "directors": [("Thomas", "Robert", "Gérant")], "employee_range": "6-9"},
    {"company_name": "Cabinet Dentaire Saint-Michel", "siren": "078901234", "naf_code": "86.23Z", "naf_label": "Pratique dentaire", "city": "Lille", "postal_code": "59000", "department": "59", "region": "Hauts-de-France", "phone": "03 20 00 00 08", "email": "secretariat@dentaire-stmichel.fr", "estimated_revenue": 22000.0, "stage_slug": "contacte", "propensity_score": 70.0, "propensity_category": "WARM", "tags": ["santé"], "directors": [("Dr.", "Moreau", "Dentiste")], "employee_range": "3-5"},
    {"company_name": "Fleuriste Les Quatre Saisons", "siren": "989012345", "naf_code": "47.76Z", "naf_label": "Commerce de détail de fleurs", "city": "Lille", "postal_code": "59000", "department": "59", "region": "Hauts-de-France", "phone": "03 20 00 00 09", "email": "boutique@4saisons-fleurs.fr", "website": "https://4saisons-fleurs.fr", "estimated_revenue": 9000.0, "stage_slug": "rdv-pris", "propensity_score": 65.0, "propensity_category": "WARM", "tags": ["retail"], "directors": [("Marie", "Petit", "Gérante")], "employee_range": "3-5"},
    {"company_name": "Auto-École Excellence", "siren": "890123456", "naf_code": "85.53Z", "naf_label": "Enseignement de la conduite", "city": "Tourcoing", "postal_code": "59200", "department": "59", "region": "Hauts-de-France", "phone": "03 20 00 00 10", "email": "contact@autoecole-excellence.fr", "website": "https://autoecole-excellence.fr", "estimated_revenue": 11000.0, "stage_slug": "negociation", "propensity_score": 75.0, "propensity_category": "HOT", "tags": ["formation"], "directors": [("Karim", "Benali", "Directeur")], "employee_range": "6-9"},
    {"company_name": "Agence Web Conseil", "siren": "789012347", "naf_code": "73.11Z", "naf_label": "Activités des agences de publicité", "city": "Paris", "postal_code": "75008", "department": "75", "region": "Île-de-France", "phone": "01 42 00 00 01", "email": "hello@web-conseil.fr", "website": "https://web-conseil.fr", "estimated_revenue": 45000.0, "stage_slug": "nouveau", "propensity_score": 82.0, "propensity_category": "HOT", "tags": ["marketing", "digital"], "directors": [("Julien", "Marchand", "CEO")], "employee_range": "10-19"},
    {"company_name": "Studio Photo Lumière", "siren": "678901248", "naf_code": "74.20Z", "naf_label": "Activités photographiques", "city": "Lyon", "postal_code": "69001", "department": "69", "region": "Auvergne-Rhône-Alpes", "phone": "04 78 00 00 02", "email": "studio@lumiere-photo.fr", "estimated_revenue": 14000.0, "stage_slug": "contacte", "propensity_score": 58.0, "propensity_category": "WARM", "tags": ["créatif"], "directors": [("Antoine", "Riviere", "Photographe")], "employee_range": "1-2"},
]

# =============================================================================
# SEQUENCES, SIGNAUX, WEBHOOKS, ABM, INBOUND
# =============================================================================

DEMO_SEQUENCES = [
    {
        "name": "Onboarding Cold Email — 5 jours",
        "description": "Séquence standard pour cold prospects, 4 emails sur 5 jours",
        "steps": [
            {"step_number": 1, "wait_days": 0, "subject_template": "{{company_name}}, une question rapide", "body_template": "Bonjour {{first_name}},\n\nJe travaille avec des entreprises comme la vôtre pour [bénéfice].\n\nÊtes-vous disponible 15 min cette semaine ?\n\nCordialement,"},
            {"step_number": 2, "wait_days": 2, "subject_template": "Rebond — {{company_name}}", "body_template": "Bonjour {{first_name}},\n\nJe n'ai pas eu de retour sur mon précédent message.\n\nUn créneau bref serait précieux.\n\nMerci,"},
            {"step_number": 3, "wait_days": 4, "subject_template": "Dernier rappel — {{company_name}}", "body_template": "{{first_name}},\n\nDernière relance de ma part.\n\nSi le sujet n'est pas pertinent, indiquez-le moi simplement.\n\nCordialement,"},
        ],
    },
    {
        "name": "Nurture Warm Leads — 3 emails",
        "description": "Pour prospects WARM en négociation",
        "steps": [
            {"step_number": 1, "wait_days": 0, "subject_template": "Étude de cas {{naf_label}}", "body_template": "Bonjour {{first_name}},\n\nNous avons aidé une entreprise similaire à atteindre [résultat].\n\nVoici l'étude de cas : [lien]\n\nQu'en pensez-vous ?"},
            {"step_number": 2, "wait_days": 3, "subject_template": "Ressource pour {{company_name}}", "body_template": "Bonjour,\n\nVoici un guide qui pourrait vous intéresser.\n\nÀ bientôt,"},
        ],
    },
]

DEMO_SIGNALS = [
    {"prospect_name": "TechWeb Solutions", "type": "job_posting_detected", "title": "5 nouvelles offres d'emploi détectées", "description": "Forte phase de recrutement — signal de croissance", "source": "scraper", "severity": "high"},
    {"prospect_name": "Restaurant Le Carillon", "type": "news_mention", "title": "Article presse — La Voix du Nord", "description": "Mention dans un article sur les nouvelles tendances culinaires", "source": "press", "severity": "medium"},
    {"prospect_name": "Avocat Conseil Lefebvre", "type": "bodacc_capital_change", "title": "Augmentation de capital +50k€", "description": "Capital social porté à 100k€ — phase d'expansion", "source": "bodacc", "severity": "high"},
    {"prospect_name": "Agence Web Conseil", "type": "website_change", "title": "Nouveau site web détecté", "description": "Refonte complète du site corporate", "source": "scraper", "severity": "medium"},
    {"prospect_name": "Boulangerie Martin", "type": "inbound_form", "title": "Formulaire de contact rempli", "description": "Demande de devis via le site", "source": "inbound", "severity": "critical"},
]

DEMO_WEBHOOKS = [
    {"name": "Slack #sales", "url": "https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXX", "events": ["prospect.created", "prospect.stage_changed"], "is_active": False},
    {"name": "Make.com — Nouveau lead", "url": "https://hook.eu1.make.com/abcdef1234567890", "events": ["prospect.created", "prospect.enriched"], "is_active": False},
]

DEMO_ABM_LISTS = [
    {"name": "ICP Tech 10-50 — Hauts-de-France", "description": "Scale-ups IT en région Hauts-de-France", "criteria": {"naf_codes": ["62.01Z", "62.02A"], "regions": ["Hauts-de-France"], "employee_min": 10, "employee_max": 50}},
    {"name": "Restaurants Premium Lille", "description": "Restaurants gastronomiques sur Lille métropole", "criteria": {"naf_codes": ["56.10A"], "departments": ["59"], "score_min": 70}},
]

DEMO_INBOUND_SOURCES = [
    {"name": "Formulaire site corporate", "source_type": "webhook", "auto_enrich": True, "field_mapping": {"email": "email", "company": "company_name", "phone": "phone"}},
    {"name": "Typeform — Demande de devis", "source_type": "typeform", "auto_enrich": True, "field_mapping": {"answers.email": "email", "answers.text_company": "company_name"}},
]


# =============================================================================
# SEED FUNCTIONS
# =============================================================================

async def seed_users(db):
    email = os.getenv("ADMIN_EMAIL", "admin@le-publicitaire.fr")
    password = os.getenv("ADMIN_PASSWORD", "Admin123")
    full_name = os.getenv("ADMIN_FULL_NAME", "Administrateur")

    existing = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if existing:
        logger.info(f"✓ User admin déjà existant : {email}")
        return existing

    user = User(email=email, full_name=full_name, hashed_password=hash_password(password), role="admin", is_active=True)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    logger.success(f"✓ Admin créé : {email}")
    return user


async def seed_stages(db):
    stages_map = {}
    for sd in DEFAULT_STAGES:
        existing = (await db.execute(select(PipelineStage).where(PipelineStage.slug == sd["slug"]))).scalar_one_or_none()
        if existing:
            stages_map[sd["slug"]] = existing
            continue
        stage = PipelineStage(**sd)
        db.add(stage)
        await db.flush()
        stages_map[sd["slug"]] = stage
        logger.info(f"  ✓ Étape : {sd['name']}")
    await db.commit()
    logger.success(f"✓ {len(stages_map)} étapes pipeline")
    return stages_map


async def seed_plugins(db):
    for pd in DEFAULT_PLUGINS:
        existing = (await db.execute(select(PluginState).where(PluginState.name == pd["name"]))).scalar_one_or_none()
        if existing:
            continue
        db.add(PluginState(**pd))
    await db.commit()
    total = (await db.execute(select(PluginState))).scalars().all()
    logger.success(f"✓ {len(total)} plugins enregistrés")


async def seed_prospects(db, stages_map):
    existing = (await db.execute(select(Prospect))).scalars().all()
    if len(existing) >= len(DEMO_PROSPECTS):
        logger.info(f"✓ Déjà {len(existing)} prospects, skip")
        return {p.company_name: p for p in existing}

    created = {}
    for pd in DEMO_PROSPECTS:
        existing_p = (await db.execute(select(Prospect).where(Prospect.siren == pd["siren"]))).scalar_one_or_none()
        if existing_p:
            created[existing_p.company_name] = existing_p
            continue

        data = {k: v for k, v in pd.items() if k not in ("directors", "stage_slug")}
        directors = pd.get("directors", [])
        stage = stages_map.get(pd["stage_slug"])

        prospect = Prospect(
            **data,
            country="FR",
            stage_id=stage.id if stage else None,
            sources_used=["seed"],
            last_enriched_at=date.today(),
            consent_given=True,
        )

        for i, (fname, lname, role) in enumerate(directors):
            prospect.contacts.append(Contact(first_name=fname, last_name=lname, role=role, is_primary=(i == 0)))

        db.add(prospect)
        created[prospect.company_name] = prospect

    await db.commit()
    logger.success(f"✓ {len(created)} prospects en base")
    return created


async def seed_sequences(db, user):
    existing = (await db.execute(select(EmailSequence))).scalars().all()
    if existing:
        logger.info(f"✓ {len(existing)} séquences déjà présentes, skip")
        return

    for sd in DEMO_SEQUENCES:
        seq = EmailSequence(name=sd["name"], description=sd["description"], is_active=True, created_by=user.id)
        db.add(seq)
        await db.flush()
        for step in sd["steps"]:
            db.add(SequenceStep(sequence_id=seq.id, **step))
    await db.commit()
    logger.success(f"✓ {len(DEMO_SEQUENCES)} séquences créées")


async def seed_signals(db, prospects_map):
    existing = (await db.execute(select(Signal))).scalars().all()
    if existing:
        logger.info(f"✓ {len(existing)} signaux déjà présents, skip")
        return

    count = 0
    for sd in DEMO_SIGNALS:
        prospect = prospects_map.get(sd["prospect_name"])
        if not prospect:
            continue
        signal = Signal(
            prospect_id=prospect.id,
            type=sd["type"],
            title=sd["title"],
            description=sd["description"],
            source=sd["source"],
            severity=sd["severity"],
            is_read=False,
            signal_date=datetime.now(timezone.utc) - timedelta(days=random.randint(0, 7)),
        )
        db.add(signal)
        count += 1
    await db.commit()
    logger.success(f"✓ {count} signaux créés")


async def seed_webhooks(db):
    existing = (await db.execute(select(Webhook))).scalars().all()
    if existing:
        logger.info(f"✓ {len(existing)} webhooks déjà présents, skip")
        return

    for wd in DEMO_WEBHOOKS:
        db.add(Webhook(**wd))
    await db.commit()
    logger.success(f"✓ {len(DEMO_WEBHOOKS)} webhooks créés")


async def seed_abm_lists(db, user, prospects_map):
    existing = (await db.execute(select(ABMList))).scalars().all()
    if existing:
        logger.info(f"✓ {len(existing)} listes ABM déjà présentes, skip")
        return

    for ld in DEMO_ABM_LISTS:
        abm = ABMList(
            name=ld["name"],
            description=ld["description"],
            criteria=ld["criteria"],
            prospects_count=random.randint(15, 250),
            created_by=user.id,
        )
        db.add(abm)
    await db.commit()
    logger.success(f"✓ {len(DEMO_ABM_LISTS)} listes ABM créées")


async def seed_inbound_sources(db):
    import secrets
    existing = (await db.execute(select(InboundSource))).scalars().all()
    if existing:
        logger.info(f"✓ {len(existing)} sources inbound déjà présentes, skip")
        return

    for sd in DEMO_INBOUND_SOURCES:
        token = f"tok_{secrets.token_urlsafe(12)}"
        db.add(InboundSource(
            name=sd["name"],
            token=token,
            source_type=sd["source_type"],
            field_mapping=sd["field_mapping"],
            auto_enrich=sd["auto_enrich"],
            is_active=True,
            leads_count=random.randint(0, 30),
        ))
    await db.commit()
    logger.success(f"✓ {len(DEMO_INBOUND_SOURCES)} sources inbound créées")


async def seed_activities(db, user, prospects_map):
    existing = (await db.execute(select(Activity))).scalars().all()
    if existing:
        logger.info(f"✓ {len(existing)} activités déjà présentes, skip")
        return

    activity_types = ["call", "email", "meeting", "note"]
    count = 0
    for name, p in list(prospects_map.items())[:6]:
        for _ in range(random.randint(1, 3)):
            db.add(Activity(
                prospect_id=p.id,
                user_id=user.id,
                type=random.choice(activity_types),
                title=f"Échange avec {name}",
                body=f"Suivi commercial — {random.choice(['discussion budget', 'présentation produit', 'envoi proposition', 'follow-up'])}",
                is_completed=True,
                completed_at=datetime.now(timezone.utc) - timedelta(days=random.randint(1, 30)),
            ))
            count += 1
    await db.commit()
    logger.success(f"✓ {count} activités créées")


# =============================================================================
# MAIN
# =============================================================================

async def main():
    logger.info("🌱 Démarrage du seed B2B Prospector...")

    async with AsyncSessionLocal() as db:
        user = await seed_users(db)
        stages_map = await seed_stages(db)
        await seed_plugins(db)
        prospects_map = await seed_prospects(db, stages_map)
        await seed_sequences(db, user)
        await seed_signals(db, prospects_map)
        await seed_webhooks(db)
        await seed_abm_lists(db, user, prospects_map)
        await seed_inbound_sources(db)
        await seed_activities(db, user, prospects_map)

    await close_db()
    logger.success("✅ Seed terminé !")


if __name__ == "__main__":
    asyncio.run(main())
