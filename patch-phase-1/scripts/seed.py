#!/usr/bin/env python3
"""
Script de seed - Données de démo pour B2B Prospector
Crée: 1 admin, 6 étapes pipeline, 10 prospects de démo, plugins activés
"""
import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

# Setup path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, delete
from passlib.context import CryptContext

# Import models
from models.database.base import Base
from models.database.prospect import Prospect
from models.database.pipeline_stage import PipelineStage
from models.database.user import User
from models.database.plugin_state import PluginState

# Config - utiliser variable d'environnement ou défaut
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/prospector"
)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def seed_database():
    """Seed the database with initial data."""
    print(f"🔌 Connexion à {DATABASE_URL}...")
    
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        print("🧹 Nettoyage des données existantes...")
        await session.execute(delete(Prospect))
        await session.execute(delete(PipelineStage))
        await session.execute(delete(User))
        await session.execute(delete(PluginState))
        await session.commit()

        # 1. Créer l'utilisateur admin
        print("👤 Création de l'admin...")
        admin = User(
            email="admin@company.com",
            username="admin",
            hashed_password=pwd_context.hash("admin"),
            full_name="Administrateur",
            role="admin",
            is_active=True,
            is_verified=True
        )
        session.add(admin)

        # 2. Créer les 6 étapes du pipeline
        print("📊 Création des étapes du pipeline...")
        stages_data = [
            ("Nouveau", "Prospect nouvellement ajouté", 0, "#3B82F6"),
            ("Contacté", "Premier contact établi", 1, "#8B5CF6"),
            ("RDV pris", "Rendez-vous programmé", 2, "#EC4899"),
            ("En négociation", "Discussion commerciale en cours", 3, "#F59E0B"),
            ("Gagné", "Contrat signé", 4, "#10B981"),
            ("Perdu", "Opportunity perdue", 5, "#EF4444"),
        ]

        stages = {}
        for name, desc, order, color in stages_data:
            stage = PipelineStage(
                name=name,
                description=desc,
                order=order,
                color=color,
                is_active=True
            )
            session.add(stage)
            stages[name] = stage

        await session.flush()

        # 3. Créer 10 prospects de démo
        print("🏢 Création de 10 prospects de démo...")
        prospects_data = [
            {
                "siren": "552081317",
                "raison_sociale": "CARREFOUR FRANCE",
                "nom_commercial": "Carrefour",
                "ville": "BOULOGNE-BILLANCOURT",
                "code_postal": "92100",
                "secteur_activite": "Commerce de détail",
                "code_naf": "47.11F",
                "effectif": "10000+",
                "email": "contact@carrefour.fr",
                "site_web": "https://www.carrefour.fr",
                "telephone": "0146101020",
                "score": 85,
                "score_label": "HOT",
                "stage_name": "Nouveau"
            },
            {
                "siren": "775684019",
                "raison_sociale": "MICHELIN",
                "nom_commercial": "Michelin",
                "ville": "CLERMONT-FERRAND",
                "code_postal": "63000",
                "secteur_activite": "Fabrication de pneumatiques",
                "code_naf": "22.11Z",
                "effectif": "5000-9999",
                "email": "info@michelin.com",
                "site_web": "https://www.michelin.fr",
                "telephone": "0473323232",
                "score": 65,
                "score_label": "WARM",
                "stage_name": "Contacté"
            },
            {
                "siren": "542065479",
                "raison_sociale": "DANONE",
                "nom_commercial": "Danone",
                "ville": "PARIS",
                "code_postal": "75015",
                "secteur_activite": "Industrie agroalimentaire",
                "code_naf": "10.51C",
                "effectif": "5000-9999",
                "email": "contact@danone.com",
                "site_web": "https://www.danone.com",
                "telephone": "0144345050",
                "score": 90,
                "score_label": "HOT",
                "stage_name": "RDV pris"
            },
            {
                "siren": "552032534",
                "raison_sociale": "SAINT-GOBAIN",
                "nom_commercial": "Saint-Gobain",
                "ville": "COURBEVOIE",
                "code_postal": "92400",
                "secteur_activite": "Matériaux de construction",
                "code_naf": "23.11Z",
                "effectif": "10000+",
                "email": "info@saint-gobain.com",
                "site_web": "https://www.saint-gobain.fr",
                "telephone": "0147623000",
                "score": 70,
                "score_label": "WARM",
                "stage_name": "En négociation"
            },
            {
                "raison_sociale": "LEGENDRE SAS",
                "nom_commercial": "Legendre",
                "ville": "LILLE",
                "code_postal": "59000",
                "secteur_activite": "BTP",
                "code_naf": "41.20A",
                "effectif": "500-999",
                "email": "contact@legendre.fr",
                "site_web": "https://www.legendre.fr",
                "telephone": "0320123456",
                "score": 40,
                "score_label": "COLD",
                "stage_name": "Nouveau"
            },
            {
                "siren": "343058140",
                "raison_sociale": "VINCI CONSTRUCTION",
                "nom_commercial": "Vinci",
                "ville": "NANTERRE",
                "code_postal": "92000",
                "secteur_activite": "Construction",
                "code_naf": "41.20B",
                "effectif": "10000+",
                "email": "info@vinci.com",
                "site_web": "https://www.vinci.com",
                "telephone": "0147163838",
                "score": 95,
                "score_label": "HOT",
                "stage_name": "Gagné"
            },
            {
                "siren": "775665604",
                "raison_sociale": "BOUYGUES CONSTRUCTION",
                "nom_commercial": "Bouygues",
                "ville": "GUYANCOURT",
                "code_postal": "78280",
                "secteur_activite": "Construction",
                "code_naf": "41.20A",
                "effectif": "5000-9999",
                "email": "contact@bouygues-construction.com",
                "site_web": "https://www.bouygues-construction.com",
                "telephone": "0130606060",
                "score": 60,
                "score_label": "WARM",
                "stage_name": "Contacté"
            },
            {
                "raison_sociale": "TECH STARTUP SAS",
                "nom_commercial": "TechStart",
                "ville": "LYON",
                "code_postal": "69002",
                "secteur_activite": "Services numériques",
                "code_naf": "62.01Z",
                "effectif": "10-49",
                "email": "hello@techstart.io",
                "site_web": "https://www.techstart.io",
                "telephone": "0478123456",
                "score": 80,
                "score_label": "HOT",
                "stage_name": "Nouveau"
            },
            {
                "raison_sociale": "CABINET MARTIN & ASSOCIES",
                "nom_commercial": "Martin Conseil",
                "ville": "BORDEAUX",
                "code_postal": "33000",
                "secteur_activite": "Conseil aux entreprises",
                "code_naf": "70.22Z",
                "effectif": "1-9",
                "email": "contact@martin-conseil.fr",
                "site_web": "https://www.martin-conseil.fr",
                "telephone": "0556123456",
                "score": 30,
                "score_label": "COLD",
                "stage_name": "Perdu"
            },
            {
                "raison_sociale": "PHARMACIE CENTRALE",
                "nom_commercial": "Pharmacie Centrale",
                "ville": "TOULOUSE",
                "code_postal": "31000",
                "secteur_activite": "Santé",
                "code_naf": "47.73Z",
                "effectif": "1-9",
                "email": "pharma.centrale@email.fr",
                "telephone": "0561123456",
                "score": 55,
                "score_label": "WARM",
                "stage_name": "RDV pris"
            }
        ]

        for pdata in prospects_data:
            stage_name = pdata.pop("stage_name", "Nouveau")
            stage = stages.get(stage_name)
            
            prospect = Prospect(
                siren=pdata.get("siren"),
                raison_sociale=pdata["raison_sociale"],
                nom_commercial=pdata.get("nom_commercial"),
                email=pdata.get("email"),
                telephone=pdata.get("telephone"),
                site_web=pdata.get("site_web"),
                adresse=None,
                code_postal=pdata.get("code_postal"),
                ville=pdata.get("ville"),
                pays="France",
                code_naf=pdata.get("code_naf"),
                libelle_naf=None,
                secteur_activite=pdata.get("secteur_activite"),
                effectif=pdata.get("effectif"),
                chiffre_affaires=None,
                stage_id=stage.id if stage else None,
                score=pdata.get("score", 0),
                score_label=pdata.get("score_label", "COLD"),
                source="seed",
                notes=None,
                metadata_json={}
            )
            session.add(prospect)

        await session.flush()

        # 4. Activer les plugins principaux
        print("🔌 Activation des plugins...")
        plugins_to_activate = [
            ("prospects", "Prospects Management"),
            ("pipeline", "Pipeline Kanban"),
            ("dashboard", "Dashboard"),
            ("system", "System"),
            ("scraper-insee", "Scraper INSEE"),
            ("audit-digital", "Audit Digital"),
            ("semantic-analyzer", "Analyse Sémantique"),
            ("predictive-scorer", "Scoring Prédictif"),
            ("automation-engine", "Moteur d'Automation"),
            ("compliance-guard", "Compliance RGPD"),
        ]

        for pname, display in plugins_to_activate:
            plugin_state = PluginState(
                name=pname,
                display_name=display,
                version="1.0.0",
                is_active=True,
                is_installed=True,
                config={}
            )
            session.add(plugin_state)

        await session.commit()

        print("\n✅ Seed terminé avec succès!")
        print(f"   - 1 utilisateur admin (admin@company.com / admin)")
        print(f"   - 6 étapes de pipeline créées")
        print(f"   - 10 prospects de démo ajoutés")
        print(f"   - {len(plugins_to_activate)} plugins activés")


if __name__ == "__main__":
    asyncio.run(seed_database())
