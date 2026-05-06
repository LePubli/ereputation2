"""Service métier pour les prospects."""
from datetime import date
from io import BytesIO
from typing import Any
from uuid import UUID

import pandas as pd
from loguru import logger
from sqlalchemy import desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.database.pipeline_stage import PipelineStage
from models.database.prospect import Contact, Prospect
from models.schemas.prospect import (
    ProspectCreate,
    ProspectImportResult,
    ProspectUpdate,
)
from services.scrapers.aggregator import EnrichmentAggregator


class ProspectService:
    """Logique métier prospects (CRUD + enrichissement)."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # READ
    # =========================================================================

    async def list_prospects(
        self,
        page: int = 1,
        page_size: int = 25,
        search: str | None = None,
        stage_id: UUID | None = None,
    ) -> tuple[list[Prospect], int]:
        offset = (page - 1) * page_size

        stmt = select(Prospect).options(selectinload(Prospect.contacts))

        if search:
            like = f"%{search.lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(Prospect.company_name).like(like),
                    Prospect.siren.like(f"{search}%"),
                    Prospect.siret.like(f"{search}%"),
                    func.lower(Prospect.city).like(like),
                )
            )

        if stage_id:
            stmt = stmt.where(Prospect.stage_id == stage_id)

        # Total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.db.execute(count_stmt)).scalar_one()

        # Pagination
        stmt = stmt.order_by(desc(Prospect.created_at)).offset(offset).limit(page_size)
        result = await self.db.execute(stmt)
        return list(result.scalars().unique().all()), total

    async def get_prospect(self, prospect_id: UUID) -> Prospect | None:
        stmt = (
            select(Prospect)
            .options(selectinload(Prospect.contacts))
            .where(Prospect.id == prospect_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    # =========================================================================
    # CREATE
    # =========================================================================

    async def create_manual(self, data: ProspectCreate) -> Prospect:
        """Création manuelle depuis le formulaire."""
        prospect = Prospect(**data.model_dump(exclude_unset=True))

        # Si pas d'étape spécifiée, on prend la première
        if not prospect.stage_id:
            prospect.stage_id = await self._get_default_stage_id()

        self.db.add(prospect)
        await self.db.commit()
        await self.db.refresh(prospect)
        return prospect

    async def create_by_identifier(self, identifier: str) -> Prospect:
        """
        Création à partir d'un SIREN/SIRET via le scraping multi-sources.

        Lève ValueError si l'enrichissement échoue (aucune source ne répond).
        """
        identifier = identifier.replace(" ", "").strip()

        # Vérifier si déjà existant
        if len(identifier) >= 9:
            siren = identifier[:9]
            stmt = select(Prospect).where(Prospect.siren == siren)
            existing = (await self.db.execute(stmt)).scalar_one_or_none()
            if existing:
                logger.info(f"Prospect {siren} déjà existant, on retourne l'existant")
                return existing

        # Enrichissement
        aggregator = EnrichmentAggregator(db=self.db)
        enrichment = await aggregator.enrich_by_siret(identifier)

        if not enrichment.get("sources_used"):
            raise ValueError(f"Aucune source n'a pu enrichir l'identifiant {identifier}")

        # Construction du prospect
        creation_date = enrichment.get("creation_date")
        if creation_date and isinstance(creation_date, str):
            try:
                creation_date = date.fromisoformat(creation_date)
            except ValueError:
                creation_date = None

        stage_id = await self._get_default_stage_id()

        prospect = Prospect(
            siren=enrichment.get("siren"),
            siret=enrichment.get("siret"),
            company_name=enrichment.get("company_name") or f"Société {identifier}",
            legal_form=enrichment.get("legal_form"),
            naf_code=enrichment.get("naf_code"),
            naf_label=enrichment.get("naf_label"),
            creation_date=creation_date,
            employee_range=enrichment.get("employee_range"),
            address=enrichment.get("address"),
            postal_code=enrichment.get("postal_code"),
            city=enrichment.get("city"),
            department=enrichment.get("department"),
            region=enrichment.get("region"),
            country="FR",
            latitude=enrichment.get("latitude"),
            longitude=enrichment.get("longitude"),
            website=enrichment.get("website"),
            phone=enrichment.get("phone"),
            stage_id=stage_id,
            enrichment=enrichment,
            sources_used=enrichment.get("sources_used", []),
            last_enriched_at=date.today(),
        )

        # Dirigeants en contacts
        directors = enrichment.get("directors") or []
        for d in directors[:3]:
            if d.get("first_name") or d.get("last_name"):
                prospect.contacts.append(
                    Contact(
                        first_name=d.get("first_name"),
                        last_name=d.get("last_name"),
                        role=d.get("role"),
                        is_primary=False,
                    )
                )

        self.db.add(prospect)
        await self.db.commit()
        await self.db.refresh(prospect)
        return prospect

    async def import_from_file(self, file_bytes: bytes, filename: str) -> ProspectImportResult:
        """Import en masse depuis CSV/XLS/XLSX."""
        ext = filename.rsplit(".", 1)[-1].lower()
        try:
            if ext == "csv":
                df = pd.read_csv(BytesIO(file_bytes), sep=None, engine="python", dtype=str)
            elif ext in ("xls", "xlsx"):
                df = pd.read_excel(BytesIO(file_bytes), dtype=str)
            else:
                raise ValueError(f"Format non supporté : {ext}")
        except Exception as e:
            return ProspectImportResult(imported=0, skipped=0, errors=[f"Lecture fichier: {e}"])

        df.columns = [c.strip().lower() for c in df.columns]

        imported = 0
        skipped = 0
        errors: list[str] = []

        stage_id = await self._get_default_stage_id()

        for idx, row in df.iterrows():
            try:
                row_dict = row.dropna().to_dict()
                company_name = (
                    row_dict.get("company_name")
                    or row_dict.get("raison_sociale")
                    or row_dict.get("nom")
                    or row_dict.get("entreprise")
                )
                siren = row_dict.get("siren")
                siret = row_dict.get("siret")

                if not company_name and not siren and not siret:
                    skipped += 1
                    continue

                # Doublon par SIREN
                if siren:
                    stmt = select(Prospect).where(Prospect.siren == str(siren)[:9])
                    if (await self.db.execute(stmt)).scalar_one_or_none():
                        skipped += 1
                        continue

                prospect = Prospect(
                    company_name=str(company_name or f"Import ligne {idx+1}"),
                    siren=str(siren)[:9] if siren else None,
                    siret=str(siret)[:14] if siret else None,
                    address=row_dict.get("address") or row_dict.get("adresse"),
                    postal_code=row_dict.get("postal_code") or row_dict.get("code_postal"),
                    city=row_dict.get("city") or row_dict.get("ville"),
                    website=row_dict.get("website") or row_dict.get("site_web"),
                    phone=row_dict.get("phone") or row_dict.get("telephone"),
                    email=row_dict.get("email"),
                    naf_code=row_dict.get("naf") or row_dict.get("naf_code"),
                    notes=row_dict.get("notes"),
                    stage_id=stage_id,
                    sources_used=["import"],
                )
                self.db.add(prospect)
                imported += 1

            except Exception as e:
                errors.append(f"Ligne {idx+1}: {e}")
                skipped += 1

        try:
            await self.db.commit()
        except Exception as e:
            await self.db.rollback()
            return ProspectImportResult(imported=0, skipped=imported + skipped, errors=[str(e)])

        return ProspectImportResult(imported=imported, skipped=skipped, errors=errors[:20])

    # =========================================================================
    # UPDATE / DELETE
    # =========================================================================

    async def update(self, prospect_id: UUID, data: ProspectUpdate) -> Prospect | None:
        prospect = await self.get_prospect(prospect_id)
        if not prospect:
            return None

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(prospect, field, value)

        await self.db.commit()
        await self.db.refresh(prospect)
        return prospect

    async def update_stage(
        self,
        prospect_id: UUID,
        stage_id: UUID,
        position: int,
    ) -> Prospect | None:
        prospect = await self.get_prospect(prospect_id)
        if not prospect:
            return None
        prospect.stage_id = stage_id
        prospect.stage_position = position
        await self.db.commit()
        await self.db.refresh(prospect)
        return prospect

    async def delete(self, prospect_id: UUID) -> bool:
        prospect = await self.get_prospect(prospect_id)
        if not prospect:
            return False
        await self.db.delete(prospect)
        await self.db.commit()
        return True

    # =========================================================================
    # ENRICH
    # =========================================================================

    async def reenrich(self, prospect_id: UUID) -> Prospect | None:
        prospect = await self.get_prospect(prospect_id)
        if not prospect or not (prospect.siren or prospect.siret):
            return prospect

        identifier = prospect.siret or prospect.siren or ""
        aggregator = EnrichmentAggregator(db=self.db)
        enrichment = await aggregator.enrich_by_siret(identifier, use_cache=False)

        # Mise à jour des champs vides uniquement
        for field in (
            "legal_form", "naf_code", "naf_label", "employee_range",
            "address", "postal_code", "city", "department", "region",
            "latitude", "longitude", "website", "phone",
        ):
            new_val = enrichment.get(field)
            if new_val and not getattr(prospect, field):
                setattr(prospect, field, new_val)

        prospect.enrichment = enrichment
        prospect.sources_used = enrichment.get("sources_used", [])
        prospect.last_enriched_at = date.today()

        await self.db.commit()
        await self.db.refresh(prospect)
        return prospect

    # =========================================================================
    # HELPERS
    # =========================================================================

    async def _get_default_stage_id(self) -> UUID | None:
        stmt = select(PipelineStage).order_by(PipelineStage.order).limit(1)
        result = await self.db.execute(stmt)
        stage = result.scalar_one_or_none()
        return stage.id if stage else None
