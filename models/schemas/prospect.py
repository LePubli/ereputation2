"""Schémas Pydantic pour les prospects."""
from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


# =============================================================================
# CONTACTS
# =============================================================================

class ContactBase(BaseModel):
    first_name: str | None = Field(None, max_length=100)
    last_name: str | None = Field(None, max_length=100)
    role: str | None = Field(None, max_length=150)
    email: EmailStr | None = None
    phone: str | None = Field(None, max_length=30)
    linkedin_url: str | None = Field(None, max_length=500)
    is_primary: bool = False


class ContactCreate(ContactBase):
    pass


class ContactRead(ContactBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    prospect_id: UUID
    created_at: datetime
    updated_at: datetime


# =============================================================================
# PROSPECT
# =============================================================================

class ProspectBase(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=500)
    siren: str | None = Field(None, pattern=r"^\d{9}$")
    siret: str | None = Field(None, pattern=r"^\d{14}$")
    legal_form: str | None = Field(None, max_length=100)
    naf_code: str | None = Field(None, max_length=10)
    naf_label: str | None = Field(None, max_length=255)
    creation_date: date | None = None
    employee_range: str | None = Field(None, max_length=50)
    capital: float | None = None

    address: str | None = Field(None, max_length=500)
    postal_code: str | None = Field(None, max_length=10)
    city: str | None = Field(None, max_length=100)
    department: str | None = Field(None, max_length=3)
    region: str | None = Field(None, max_length=100)
    country: str = Field("FR", max_length=2)
    latitude: float | None = None
    longitude: float | None = None

    website: str | None = Field(None, max_length=500)
    phone: str | None = Field(None, max_length=30)
    email: EmailStr | None = None

    notes: str | None = None
    tags: list[str] = Field(default_factory=list)


class ProspectCreate(ProspectBase):
    """Création manuelle d'un prospect (formulaire complet)."""
    stage_id: UUID | None = None


class ProspectCreateBySiret(BaseModel):
    """Création par SIRET ou SIREN (le scraper fait le reste)."""
    identifier: str = Field(..., description="SIREN (9 chiffres) ou SIRET (14 chiffres)")

    @field_validator("identifier")
    @classmethod
    def validate_identifier(cls, v: str) -> str:
        v = v.replace(" ", "").strip()
        if not v.isdigit():
            raise ValueError("L'identifiant doit contenir uniquement des chiffres")
        if len(v) not in (9, 14):
            raise ValueError("L'identifiant doit contenir 9 (SIREN) ou 14 (SIRET) chiffres")
        return v


class ProspectUpdate(BaseModel):
    """Patch d'un prospect (tous les champs optionnels)."""
    company_name: str | None = Field(None, min_length=1, max_length=500)
    legal_form: str | None = None
    naf_code: str | None = None
    naf_label: str | None = None
    employee_range: str | None = None
    capital: float | None = None
    address: str | None = None
    postal_code: str | None = None
    city: str | None = None
    department: str | None = None
    region: str | None = None
    website: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    notes: str | None = None
    tags: list[str] | None = None
    stage_id: UUID | None = None
    consent_given: bool | None = None
    opt_out: bool | None = None


class ProspectStageUpdate(BaseModel):
    """Pour le drag-n-drop : changement d'étape."""
    stage_id: UUID
    position: int = 0


class ProspectRead(ProspectBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    stage_id: UUID | None
    stage_position: int
    digital_score: float | None
    propensity_score: float | None
    propensity_category: str | None
    enrichment: dict[str, Any]
    sources_used: list[str]
    last_enriched_at: date | None
    estimated_revenue: float | None
    consent_given: bool
    opt_out: bool
    created_at: datetime
    updated_at: datetime
    contacts: list[ContactRead] = Field(default_factory=list)


class ProspectListResponse(BaseModel):
    items: list[ProspectRead]
    total: int
    page: int
    page_size: int


class ProspectImportResult(BaseModel):
    """Retour du POST /import (CSV/XLSX)."""
    imported: int
    skipped: int
    errors: list[str] = Field(default_factory=list)
