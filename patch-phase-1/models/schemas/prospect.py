"""
Pydantic schemas for Prospect API.
"""
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime


class ProspectBase(BaseModel):
    """Base schema for Prospect."""
    raison_sociale: str = Field(..., min_length=1, max_length=255)
    nom_commercial: Optional[str] = Field(None, max_length=255)
    email: Optional[EmailStr] = None
    telephone: Optional[str] = Field(None, max_length=20)
    site_web: Optional[str] = Field(None, max_length=255)
    adresse: Optional[str] = Field(None, max_length=500)
    code_postal: Optional[str] = Field(None, max_length=10)
    ville: Optional[str] = Field(None, max_length=100)
    pays: Optional[str] = "France"
    code_naf: Optional[str] = Field(None, max_length=10)
    libelle_naf: Optional[str] = Field(None, max_length=255)
    secteur_activite: Optional[str] = Field(None, max_length=255)
    effectif: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None


class ProspectCreate(ProspectBase):
    """Schema for creating a Prospect."""
    siren: Optional[str] = Field(None, min_length=9, max_length=9)
    siret: Optional[str] = Field(None, min_length=14, max_length=14)
    source: Optional[str] = "manual"
    stage_id: Optional[int] = 1
    metadata_json: Optional[Dict[str, Any]] = None


class ProspectUpdate(BaseModel):
    """Schema for updating a Prospect."""
    raison_sociale: Optional[str] = Field(None, min_length=1, max_length=255)
    nom_commercial: Optional[str] = Field(None, max_length=255)
    email: Optional[EmailStr] = None
    telephone: Optional[str] = Field(None, max_length=20)
    site_web: Optional[str] = Field(None, max_length=255)
    adresse: Optional[str] = Field(None, max_length=500)
    code_postal: Optional[str] = Field(None, max_length=10)
    ville: Optional[str] = Field(None, max_length=100)
    pays: Optional[str] = None
    code_naf: Optional[str] = Field(None, max_length=10)
    libelle_naf: Optional[str] = Field(None, max_length=255)
    secteur_activite: Optional[str] = Field(None, max_length=255)
    effectif: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None
    stage_id: Optional[int] = None
    score: Optional[int] = Field(None, ge=0, le=100)
    score_label: Optional[str] = None


class ProspectResponse(ProspectBase):
    """Schema for Prospect response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    siren: Optional[str] = None
    siret: Optional[str] = None
    stage_id: Optional[int] = None
    score: int = 0
    score_label: str = "COLD"
    source: str = "manual"
    metadata_json: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class ProspectInList(BaseModel):
    """Schema for Prospect in list view."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    raison_sociale: str
    nom_commercial: Optional[str] = None
    email: Optional[str] = None
    telephone: Optional[str] = None
    ville: Optional[str] = None
    stage_id: Optional[int] = None
    score: int = 0
    score_label: str = "COLD"
    created_at: datetime


class ProspectSearch(BaseModel):
    """Schema for searching prospects."""
    query: Optional[str] = None
    stage_id: Optional[int] = None
    score_label: Optional[str] = None
    page: int = 1
    page_size: int = 20
