"""
Prospect model for B2B Prospector.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base


class Prospect(Base):
    """Prospect model representing a company/lead."""
    __tablename__ = "prospects"

    id = Column(Integer, primary_key=True, index=True)
    
    # Company info
    siren = Column(String(9), unique=True, index=True, nullable=True)
    siret = Column(String(14), unique=True, index=True, nullable=True)
    raison_sociale = Column(String(255), nullable=False)
    nom_commercial = Column(String(255), nullable=True)
    
    # Contact info
    email = Column(String(255), nullable=True)
    telephone = Column(String(20), nullable=True)
    site_web = Column(String(255), nullable=True)
    
    # Address
    adresse = Column(String(500), nullable=True)
    code_postal = Column(String(10), nullable=True)
    ville = Column(String(100), nullable=True)
    pays = Column(String(100), default="France", nullable=True)
    
    # Business info
    code_naf = Column(String(10), nullable=True)
    libelle_naf = Column(String(255), nullable=True)
    secteur_activite = Column(String(255), nullable=True)
    effectif = Column(String(50), nullable=True)
    chiffre_affaires = Column(String(50), nullable=True)
    
    # Pipeline
    stage_id = Column(Integer, ForeignKey("pipeline_stages.id"), default=1)
    stage = relationship("PipelineStage", back_populates="prospects")
    
    # Scoring
    score = Column(Integer, default=0)  # 0-100
    score_label = Column(String(20), default="COLD")  # HOT, WARM, COLD
    
    # Metadata
    source = Column(String(50), default="manual")  # manual, insee, pappers, etc.
    notes = Column(Text, nullable=True)
    metadata_json = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    audit_logs = relationship("AuditLog", back_populates="prospect")

    def __repr__(self):
        return f"<Prospect(id={self.id}, raison_sociale='{self.raison_sociale}', stage='{self.stage_id}')>"
