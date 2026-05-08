"""Service métier prospects — Phase 2."""
from datetime import date
from io import BytesIO
from typing import Any
from uuid import UUID

import pandas as pd
from loguru import logger
from sqlalchemy import and_, desc, asc, func, or_, select, cast
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.database.pipeline_stage import PipelineStage
from models.database.prospect import Contact, Prospect
from models.schemas.prospect import (
    ProspectCreate, ProspectImportResult, ProspectUpdate,
)
from services.scrapers.aggregator import EnrichmentAggregator


class ProspectService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # LIST — filtres avancés Phase 2
    # =========================================================================

    async def list_prospects(
        self,
        page: int = 1,
        page_size: int = 25,
        search: str | None = None,
        stage_id: UUID | None = None,
        # Nouveaux filtres Phase 2
        naf_code: str | None = None,
        region: str | None = None,
        department: str | None = None,
        propensity_category: str | None = None,
        source: str | None = None,
        has_website: bool | None = None,
        has_phone: bool | None = None,
        min_score: float | None = None,
        tags: list[str] | None = None,
        sort_by: str = "created_at",
        sort_dir: str = "desc",
    ) -> tuple[list[Prospect], int]:
        offset = (page - 1) * page_size

        stmt = select(Prospect).options(selectinload(Prospect.contacts))
        conditions = []

        if search:
            like = f"%{search.lower()}%"
            conditions.append(or_(
                func.lower(Prospect.company_name).like(like),
                Prospect.siren.like(f"{search}%"),
                func.lower(Prospect.city).like(like),
            ))
        if stage_id:
            conditions.append(Prospect.stage_id == stage_id)
        if naf_code:
            conditions.append(Prospect.naf_code.ilike(f"{naf_code}%"))
        if region:
            conditions.append(func.lower(Prospect.region).like(f"%{region.lower()}%"))
        if department:
            conditions.append(Prospect.department == department)
        if propensity_category:
            conditions.append(Prospect.propensity_category == propensity_category)
        if source:
            conditions.append(Prospect.source == source)
        if has_website is True:
            conditions.append(Prospect.website.isnot(None))
        if has_website is False:
            conditions.append(Prospect.website.is_(None))
        if has_phone is True:
            conditions.append(Prospect.phone.isnot(None))
        if has_phone is False:
            conditions.append(Prospect.phone.is_(None))
        if min_score is not None:
            conditions.append(Prospect.propensity_score >= min_score)
        if tags:
            for tag in tags:
                conditions.append(
                    cast(Prospect.tags, JSONB).contains([tag])
                )

        if conditions:
            stmt = stmt.where(and_(*conditions))

        # Total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.db.execute(count_stmt)).scalar_one()

        # Tri
        sort_col = getattr(Prospect, sort_by, Prospect.created_at)
        sort_fn = desc if sort_dir == "desc" else asc
        stmt = stmt.order_by(sort_fn(sort_col)).offset(offset).limit(page_size)

        result = await self.db.execute(stmt)
        return list(result.scalars().unique().all()), total

    # =========================================================================
    # GET
    # =========================================================================

    async def get_prospect(self, prospect_id: UUID) -> Prospect | None:
        stmt = (
            select(Prospect)
            .options(selectinload(Prospect.contacts))
            .where(Prospect.id == prospect_id)
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    # =========================================================================
    # CREATE
    # =========================================================================

    async def create_manual(self, data: ProspectCreate) -> Prospect:
        prospect = Prospect(**data.model_dump(exclude_unset=True), source="manual")
        if not prospect.stage_id:
            prospect.stage_id = await self._get_default_stage_id()
        self.db.add(prospect)
        await self.db.commit()
        await self.db.refresh(prospect)
        return prospect

    async def create_by_identifier(
        self,
        identifier: str,
        fast_only: bool = False,
    ) -> Prospect:
        """
        Crée par SIREN/SIRET.

        fast_only=True : utilise uniquement INSEE + BODACC (rapides).
        Les sources lentes (PJ, Maps) sont laissées au worker ARQ.
        """
        identifier = identifier.replace(" ", "").strip()

        if len(identifier) >= 9:
            siren = identifier[:9]
            existing = (await self.db.execute(
                select(Prospect).where(Prospect.siren == siren)
            )).scalar_one_or_none()
            if existing:
                return existing

        sources = ["insee", "bodacc"] if fast_only else None
        aggregator = EnrichmentAggregator(db=self.db)
        enrichment = await aggregator.enrich_by_siret(identifier, sources=sources)

        if not enrichment.get("sources_used"):
            raise ValueError(f"Aucune source disponible pour {identifier}")

        creation_date = enrichment.get("creation_date")
        if creation_date and isinstance(creation_date, str):
            try:
                creation_date = date.fromisoformat(creation_date[:10])
            except ValueError:
                creation_date = None

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
            stage_id=await self._get_default_stage_id(),
            enrichment=enrichment,
            sources_used=enrichment.get("sources_used", []),
            last_enriched_at=date.today(),
            source="siret",
        )

        # Contacts depuis INSEE
        for d in (enrichment.get("directors") or [])[:3]:
            if d.get("first_name") or d.get("last_name"):
                prospect.contacts.append(Contact(
                    first_name=d.get("first_name"),
                    last_name=d.get("last_name"),
                    role=d.get("role"),
                    is_primary=False,
                ))

        self.db.add(prospect)
        await self.db.commit()
        await self.db.refresh(prospect)
        return prospect

    async def import_from_file(self, file_bytes: bytes, filename: str) -> ProspectImportResult:
        ext = filename.rsplit(".", 1)[-1].lower()
        try:
            if ext == "csv":
                df = pd.read_csv(BytesIO(file_bytes), sep=None, engine="python", dtype=str)
            elif ext in ("xls", "xlsx"):
                df = pd.read_excel(BytesIO(file_bytes), dtype=str)
            else:
                raise ValueError(f"Format non supporté : {ext}")
        except Exception as e:
            return ProspectImportResult(imported=0, skipped=0, errors=[str(e)])

        df.columns = [c.strip().lower() for c in df.columns]
        imported, skipped, errors = 0, 0, []
        stage_id = await self._get_default_stage_id()

        for idx, row in df.iterrows():
            try:
                row_dict = row.dropna().to_dict()
                company_name = (row_dict.get("company_name") or row_dict.get("raison_sociale")
                                or row_dict.get("nom") or row_dict.get("entreprise"))
                siren = row_dict.get("siren")
                if not company_name and not siren:
                    skipped += 1
                    continue
                if siren and (await self.db.execute(
                    select(Prospect).where(Prospect.siren == str(siren)[:9])
                )).scalar_one_or_none():
                    skipped += 1
                    continue

                prospect = Prospect(
                    company_name=str(company_name or f"Import {idx+1}"),
                    siren=str(siren)[:9] if siren else None,
                    siret=str(row_dict["siret"])[:14] if "siret" in row_dict else None,
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
                    source="import",
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
    # UPDATE / DELETE / ENRICH
    # =========================================================================

    async def update(self, prospect_id: UUID, data: ProspectUpdate) -> Prospect | None:
        p = await self.get_prospect(prospect_id)
        if not p:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(p, field, value)
        await self.db.commit()
        await self.db.refresh(p)
        return p

    async def update_stage(self, prospect_id: UUID, stage_id: UUID, position: int) -> Prospect | None:
        p = await self.get_prospect(prospect_id)
        if not p:
            return None
        p.stage_id = stage_id
        p.stage_position = position
        await self.db.commit()
        await self.db.refresh(p)
        return p

    async def delete(self, prospect_id: UUID) -> bool:
        p = await self.get_prospect(prospect_id)
        if not p:
            return False
        await self.db.delete(p)
        await self.db.commit()
        return True

    async def reenrich(self, prospect_id: UUID) -> Prospect | None:
        p = await self.get_prospect(prospect_id)
        if not p or not (p.siren or p.siret):
            return p
        aggregator = EnrichmentAggregator(db=self.db)
        enrichment = await aggregator.enrich_by_siret(p.siret or p.siren or "", use_cache=False)
        for field in ("legal_form", "naf_code", "naf_label", "employee_range",
                      "address", "postal_code", "city", "department", "region",
                      "latitude", "longitude", "website", "phone"):
            new_val = enrichment.get(field)
            if new_val and not getattr(p, field):
                setattr(p, field, new_val)
        p.enrichment = enrichment
        p.sources_used = enrichment.get("sources_used", [])
        p.last_enriched_at = date.today()
        await self.db.commit()
        await self.db.refresh(p)
        return p

    async def _get_default_stage_id(self) -> UUID | None:
        stmt = select(PipelineStage).order_by(PipelineStage.order).limit(1)
        stage = (await self.db.execute(stmt)).scalar_one_or_none()
        return stage.id if stage else None
