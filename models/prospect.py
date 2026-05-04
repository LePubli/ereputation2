"""
Modèles de données SQLAlchemy pour les prospects
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, Text, JSON, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Prospect(Base):
    """Table principale des prospects"""
    __tablename__ = "prospects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    siren: Mapped[str] = mapped_column(String(9), unique=True, nullable=False, index=True)
    siret: Mapped[Optional[str]] = mapped_column(String(14), nullable=True)
    
    # Informations légales
    raison_sociale: Mapped[str] = mapped_column(String(255), nullable=False)
    nom_commercial: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    forme_juridique: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    code_naf: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    libelle_naf: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Adresse
    adresse: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    code_postal: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    ville: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    pays: Mapped[str] = mapped_column(String(2), default="FR")
    
    # Données financières
    effectif: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tranche_effectif: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    capital_social: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    chiffre_affaires: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Statut
    actif: Mapped[bool] = mapped_column(Boolean, default=True)
    date_creation: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    date_radiation: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Métadonnées
    source: Mapped[str] = mapped_column(String(50), default="insee")
    derniere_maj: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    audits: Mapped[List["DigitalAudit"]] = relationship("DigitalAudit", back_populates="prospect", cascade="all, delete-orphan")
    angles: Mapped[List["CommercialAngle"]] = relationship("CommercialAngle", back_populates="prospect", cascade="all, delete-orphan")
    interactions: Mapped[List["Interaction"]] = relationship("Interaction", back_populates="prospect", cascade="all, delete-orphan")
    scores: Mapped[List["PredictiveScore"]] = relationship("PredictiveScore", back_populates="prospect", cascade="all, delete-orphan")
    sequences: Mapped[List["OutreachSequence"]] = relationship("OutreachSequence", back_populates="prospect", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Prospect(siren='{self.siren}', raison_sociale='{self.raison_sociale}')>"


class DigitalAudit(Base):
    """Audit digital d'un prospect"""
    __tablename__ = "digital_audits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    prospect_id: Mapped[int] = mapped_column(Integer, ForeignKey("prospects.id"), nullable=False)
    
    # Site web
    url_site: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    cms_detecte: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    hebergeur: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    https_actif: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Performance
    score_performance: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    lcp: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    fid: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cls: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # SEO
    meta_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    meta_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    h1_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sitemap_present: Mapped[bool] = mapped_column(Boolean, default=False)
    robots_present: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Tracking & Pixels
    google_analytics: Mapped[bool] = mapped_column(Boolean, default=False)
    meta_pixel: Mapped[bool] = mapped_column(Boolean, default=False)
    hotjar: Mapped[bool] = mapped_column(Boolean, default=False)
    gtm: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Réseaux sociaux détectés
    linkedin_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    facebook_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    twitter_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    instagram_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Email & Conformité
    spf_configured: Mapped[bool] = mapped_column(Boolean, default=False)
    dkim_configured: Mapped[bool] = mapped_column(Boolean, default=False)
    dmarc_configured: Mapped[bool] = mapped_column(Boolean, default=False)
    rgpd_compliant: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Score global
    score_maturite: Mapped[int] = mapped_column(Integer, default=0)
    
    # Données brutes
    donnees_brutes: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Timestamps
    date_audit: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relation
    prospect: Mapped["Prospect"] = relationship("Prospect", back_populates="audits")

    def __repr__(self):
        return f"<DigitalAudit(prospect_id={self.prospect_id}, score={self.score_maturite})>"


class CommercialAngle(Base):
    """Angles commerciaux générés"""
    __tablename__ = "commercial_angles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    prospect_id: Mapped[int] = mapped_column(Integer, ForeignKey("prospects.id"), nullable=False)
    
    # Contenu de l'angle
    titre: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    categorie: Mapped[str] = mapped_column(String(50), nullable=False)  # pain_point, opportunite, conformite
    
    # Scoring
    score_priorite: Mapped[int] = mapped_column(Integer, default=0)
    score_relevance: Mapped[int] = mapped_column(Integer, default=0)
    score_urgence: Mapped[int] = mapped_column(Integer, default=0)
    score_global: Mapped[int] = mapped_column(Integer, default=0)
    
    # Preuves et sources
    faits_support: Mapped[List[dict]] = mapped_column(JSON, default=list)
    sources: Mapped[List[str]] = mapped_column(JSON, default=list)
    
    # Recommandations
    recommandation_action: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    template_suggere: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Statut
    utilise: Mapped[bool] = mapped_column(Boolean, default=False)
    date_generation: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relation
    prospect: Mapped["Prospect"] = relationship("Prospect", back_populates="angles")

    def __repr__(self):
        return f"<CommercialAngle(titre='{self.titre}', score={self.score_global})>"


class Interaction(Base):
    """Historique des interactions avec un prospect"""
    __tablename__ = "interactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    prospect_id: Mapped[int] = mapped_column(Integer, ForeignKey("prospects.id"), nullable=False)
    
    # Type d'interaction
    type_interaction: Mapped[str] = mapped_column(String(50), nullable=False)  # email, call, linkedin, whatsapp, meeting
    canal: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Contenu
    sujet: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contenu: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    piece_jointe_urls: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    
    # Statut et résultat
    statut: Mapped[str] = mapped_column(String(50), default="sent")  # sent, delivered, opened, clicked, replied
    resultat: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Métadonnées
    envoye_par: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    angle_utilise_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("commercial_angles.id"), nullable=True)
    
    # Timestamps
    date_interaction: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    date_ouverture: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    date_clic: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    date_reponse: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relations
    prospect: Mapped["Prospect"] = relationship("Prospect", back_populates="interactions")

    def __repr__(self):
        return f"<Interaction(type='{self.type_interaction}', statut='{self.statut}')>"


class PredictiveScore(Base):
    """Scores prédictifs de propension à l'achat"""
    __tablename__ = "predictive_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    prospect_id: Mapped[int] = mapped_column(Integer, ForeignKey("prospects.id"), nullable=False)
    
    # Scores par dimension
    score_digital: Mapped[int] = mapped_column(Integer, default=0)  # 0-100
    score_financier: Mapped[int] = mapped_column(Integer, default=0)  # 0-100
    score_douleurs: Mapped[int] = mapped_column(Integer, default=0)  # 0-100
    score_engagement: Mapped[int] = mapped_column(Integer, default=0)  # 0-100
    
    # Score global pondéré
    score_global: Mapped[int] = mapped_column(Integer, default=0)  # 0-100
    
    # Catégorisation
    categorie: Mapped[str] = mapped_column(String(10), default="COLD")  # HOT, WARM, COLD
    
    # Explications
    facteurs_positifs: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    facteurs_negatifs: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    recommandations: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    
    # Versioning du modèle
    modele_version: Mapped[str] = mapped_column(String(20), default="rules-v1")
    date_calcul: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relation
    prospect: Mapped["Prospect"] = relationship("Prospect", back_populates="scores")

    def __repr__(self):
        return f"<PredictiveScore(prospect_id={self.prospect_id}, global={self.score_global}, categorie={self.categorie})>"


class OutreachSequence(Base):
    """Séquences d'outreach multi-canal"""
    __tablename__ = "outreach_sequences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    prospect_id: Mapped[int] = mapped_column(Integer, ForeignKey("prospects.id"), nullable=False)
    
    # Configuration
    nom_sequence: Mapped[str] = mapped_column(String(100), nullable=False)
    type_sequence: Mapped[str] = mapped_column(String(50), nullable=False)  # standard, aggressive, nurturing
    
    # Étapes
    etapes: Mapped[List[dict]] = mapped_column(JSON, default=list)  # [{jour: 0, canal: "email", template: "..."}, ...]
    etape_actuelle: Mapped[int] = mapped_column(Integer, default=0)
    
    # Statut
    statut: Mapped[str] = mapped_column(String(20), default="pending")  # pending, running, paused, completed, stopped
    raison_arret: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Performance
    emails_envoyes: Mapped[int] = mapped_column(Integer, default=0)
    taux_ouverture: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    taux_reponse: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Timestamps
    date_debut: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    date_fin: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    date_creation: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relation
    prospect: Mapped["Prospect"] = relationship("Prospect", back_populates="sequences")

    def __repr__(self):
        return f"<OutreachSequence(nom='{self.nom_sequence}', statut='{self.statut}')>"
