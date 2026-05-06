"""
Prospect service for business logic.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import List, Optional, Dict, Any
import httpx
import hashlib
import json

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from models.database.prospect import Prospect
from models.database.pipeline_stage import PipelineStage
from models.database.scrape_cache import ScrapeCache
from models.schemas.prospect import ProspectCreate, ProspectUpdate


class ProspectService:
    """Service for prospect operations."""
    
    INSEE_API_URL = "https://recherche-entreprises.api.gouv.fr"
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_prospect(self, prospect_id: int) -> Optional[Prospect]:
        """Get a prospect by ID."""
        result = await self.db.execute(
            select(Prospect).where(Prospect.id == prospect_id)
        )
        return result.scalar_one_or_none()
    
    async def get_prospects(
        self,
        page: int = 1,
        page_size: int = 20,
        query: Optional[str] = None,
        stage_id: Optional[int] = None,
    ) -> tuple[List[Prospect], int]:
        """Get paginated list of prospects with optional filters."""
        # Build base query
        stmt = select(Prospect)
        
        # Apply filters
        if query:
            search_filter = or_(
                Prospect.raison_sociale.ilike(f"%{query}%"),
                Prospect.nom_commercial.ilike(f"%{query}%"),
                Prospect.email.ilike(f"%{query}%"),
                Prospect.siren.ilike(f"%{query}%"),
            )
            stmt = stmt.where(search_filter)
        
        if stage_id is not None:
            stmt = stmt.where(Prospect.stage_id == stage_id)
        
        # Get total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0
        
        # Apply pagination
        offset = (page - 1) * page_size
        stmt = stmt.order_by(Prospect.created_at.desc()).offset(offset).limit(page_size)
        
        result = await self.db.execute(stmt)
        prospects = result.scalars().all()
        
        return list(prospects), total
    
    async def create_prospect(self, data: ProspectCreate) -> Prospect:
        """Create a new prospect."""
        prospect = Prospect(**data.model_dump())
        self.db.add(prospect)
        await self.db.flush()
        await self.db.refresh(prospect)
        return prospect
    
    async def update_prospect(
        self, prospect_id: int, data: ProspectUpdate
    ) -> Optional[Prospect]:
        """Update an existing prospect."""
        prospect = await self.get_prospect(prospect_id)
        if not prospect:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(prospect, field, value)
        
        await self.db.flush()
        await self.db.refresh(prospect)
        return prospect
    
    async def delete_prospect(self, prospect_id: int) -> bool:
        """Delete a prospect."""
        prospect = await self.get_prospect(prospect_id)
        if not prospect:
            return False
        
        await self.db.delete(prospect)
        await self.db.flush()
        return True
    
    async def update_stage(self, prospect_id: int, stage_id: int) -> Optional[Prospect]:
        """Update prospect stage (for Kanban drag-n-drop)."""
        prospect = await self.get_prospect(prospect_id)
        if not prospect:
            return None
        
        prospect.stage_id = stage_id
        await self.db.flush()
        await self.db.refresh(prospect)
        return prospect
    
    async def fetch_from_insee(self, siren: str) -> Optional[Dict[str, Any]]:
        """Fetch company data from INSEE API (no key required)."""
        # Check cache first
        cache_key = hashlib.sha256(f"insee:{siren}".encode()).hexdigest()
        cache_result = await self.db.execute(
            select(ScrapeCache).where(ScrapeCache.query_hash == cache_key)
        )
        cached = cache_result.scalar_one_or_none()
        
        if cached and not cached.is_expired():
            return cached.response_data
        
        # Fetch from API
        url = f"{self.INSEE_API_URL}/search?q={siren}&per_page=1"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
                
                if data.get("results"):
                    company = data["results"][0]
                    result = self._parse_insee_response(company)
                    
                    # Cache the result
                    cache_entry = ScrapeCache(
                        source="insee",
                        query=siren,
                        query_hash=cache_key,
                        response_data=result,
                        expires_at=ScrapeCache.get_expiry(hours=24),
                    )
                    self.db.add(cache_entry)
                    await self.db.flush()
                    
                    return result
        except Exception as e:
            # Log error but don't fail
            print(f"INSEE fetch error: {e}")
        
        return None
    
    def _parse_insee_response(self, company: Dict) -> Dict[str, Any]:
        """Parse INSEE API response to prospect data."""
        etablissement = company.get("etablissements", [{}])[0] if company.get("etablissements") else {}
        
        return {
            "siren": company.get("siren"),
            "siret": etablissement.get("siret"),
            "raison_sociale": company.get("nom_complet", ""),
            "nom_commercial": company.get("nom_commercial"),
            "email": None,  # Not available in INSEE
            "telephone": etablissement.get("telephone"),
            "site_web": company.get("site_internet"),
            "adresse": etablissement.get("adresse"),
            "code_postal": etablissement.get("code_postal"),
            "ville": etablissement.get("commune"),
            "code_naf": etablissement.get("activite_principale"),
            "libelle_naf": etablissement.get("libelle_activite_principale"),
            "effectif": etablissement.get("tranche_effectif_salarie"),
            "metadata_json": {
                "date_creation": company.get("date_creation"),
                "categorie_entreprise": company.get("categorie_entreprise"),
            },
        }
