"""
Repositories SQLAlchemy pour la gestion des données
Implémente les patterns Repository pour un accès aux données propre et testable
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from loguru import logger

from models.prospect import (
    Prospect,
    DigitalAudit,
    CommercialAngle,
    Interaction,
    PredictiveScore,
    OutreachSequence
)


class BaseRepository:
    """Repository de base avec opérations CRUD génériques"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, model_class, id: int) -> Optional[Any]:
        """Récupère un objet par son ID"""
        result = await self.session.execute(
            select(model_class).where(model_class.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_all(self, model_class, limit: int = 100, offset: int = 0) -> List[Any]:
        """Récupère tous les objets avec pagination"""
        result = await self.session.execute(
            select(model_class).limit(limit).offset(offset)
        )
        return list(result.scalars().all())
    
    async def create(self, obj: Any) -> Any:
        """Crée un nouvel objet"""
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj
    
    async def update(self, obj: Any, **kwargs) -> Any:
        """Met à jour un objet existant"""
        for key, value in kwargs.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj
    
    async def delete(self, obj: Any) -> bool:
        """Supprime un objet"""
        await self.session.delete(obj)
        await self.session.commit()
        return True


class ProspectRepository(BaseRepository):
    """Repository pour les prospects"""
    
    async def get_by_siren(self, siren: str) -> Optional[Prospect]:
        """Récupère un prospect par son SIREN"""
        result = await self.session.execute(
            select(Prospect).where(Prospect.siren == siren)
        )
        return result.scalar_one_or_none()
    
    async def get_by_siret(self, siret: str) -> Optional[Prospect]:
        """Récupère un prospect par son SIRET"""
        result = await self.session.execute(
            select(Prospect).where(Prospect.siret == siret)
        )
        return result.scalar_one_or_none()
    
    async def search(
        self,
        query: Optional[str] = None,
        code_naf: Optional[str] = None,
        ville: Optional[str] = None,
        effectif_min: Optional[int] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Prospect]:
        """Recherche avancée de prospects"""
        stmt = select(Prospect)
        
        if query:
            stmt = stmt.where(
                (Prospect.raison_sociale.ilike(f"%{query}%")) |
                (Prospect.nom_commercial.ilike(f"%{query}%"))
            )
        
        if code_naf:
            stmt = stmt.where(Prospect.code_naf == code_naf)
        
        if ville:
            stmt = stmt.where(Prospect.ville.ilike(f"%{ville}%"))
        
        if effectif_min is not None:
            stmt = stmt.where(Prospect.effectif >= effectif_min)
        
        stmt = stmt.limit(limit).offset(offset)
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_with_relations(self, prospect_id: int) -> Optional[Prospect]:
        """Récupère un prospect avec toutes ses relations"""
        result = await self.session.execute(
            select(Prospect)
            .options(
                selectinload(Prospect.audits),
                selectinload(Prospect.angles),
                selectinload(Prospect.interactions),
                selectinload(Prospect.scores),
                selectinload(Prospect.sequences)
            )
            .where(Prospect.id == prospect_id)
        )
        return result.scalar_one_or_none()
    
    async def count(self) -> int:
        """Compte le nombre total de prospects"""
        result = await self.session.execute(select(Prospect.id))
        return len(result.scalars().all())
    
    async def get_actifs_only(self, limit: int = 100) -> List[Prospect]:
        """Récupère uniquement les prospects actifs"""
        result = await self.session.execute(
            select(Prospect).where(Prospect.actif == True).limit(limit)
        )
        return list(result.scalars().all())


class DigitalAuditRepository(BaseRepository):
    """Repository pour les audits digitaux"""
    
    async def get_by_prospect(self, prospect_id: int) -> Optional[DigitalAudit]:
        """Récupère le dernier audit d'un prospect"""
        result = await self.session.execute(
            select(DigitalAudit)
            .where(DigitalAudit.prospect_id == prospect_id)
            .order_by(DigitalAudit.date_audit.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    async def create_or_update(
        self,
        prospect_id: int,
        audit_data: Dict[str, Any]
    ) -> DigitalAudit:
        """Crée ou met à jour un audit pour un prospect"""
        existing = await self.get_by_prospect(prospect_id)
        
        if existing:
            # Met à jour l'existant
            for key, value in audit_data.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            await self.session.commit()
            await self.session.refresh(existing)
            return existing
        else:
            # Crée un nouveau
            new_audit = DigitalAudit(
                prospect_id=prospect_id,
                **audit_data,
                date_audit=datetime.utcnow()
            )
            self.session.add(new_audit)
            await self.session.commit()
            await self.session.refresh(new_audit)
            return new_audit
    
    async def get_low_scores(self, min_score: int = 0, max_score: int = 30) -> List[DigitalAudit]:
        """Récupère les audits avec un faible score de maturité"""
        result = await self.session.execute(
            select(DigitalAudit)
            .where(DigitalAudit.score_maturite.between(min_score, max_score))
            .order_by(DigitalAudit.score_maturite.asc())
        )
        return list(result.scalars().all())


class CommercialAngleRepository(BaseRepository):
    """Repository pour les angles commerciaux"""
    
    async def get_by_prospect(self, prospect_id: int) -> List[CommercialAngle]:
        """Récupère tous les angles commerciaux d'un prospect"""
        result = await self.session.execute(
            select(CommercialAngle)
            .where(CommercialAngle.prospect_id == prospect_id)
            .order_by(CommercialAngle.score_global.desc())
        )
        return list(result.scalars().all())
    
    async def get_best_angle(self, prospect_id: int) -> Optional[CommercialAngle]:
        """Récupère le meilleur angle commercial pour un prospect"""
        result = await self.session.execute(
            select(CommercialAngle)
            .where(CommercialAngle.prospect_id == prospect_id)
            .order_by(CommercialAngle.score_global.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    async def get_unused_angles(self, prospect_id: int) -> List[CommercialAngle]:
        """Récupère les angles commerciaux non encore utilisés"""
        result = await self.session.execute(
            select(CommercialAngle)
            .where(
                (CommercialAngle.prospect_id == prospect_id) &
                (CommercialAngle.utilise == False)
            )
            .order_by(CommercialAngle.score_global.desc())
        )
        return list(result.scalars().all())


class PredictiveScoreRepository(BaseRepository):
    """Repository pour les scores prédictifs"""
    
    async def get_latest_by_prospect(self, prospect_id: int) -> Optional[PredictiveScore]:
        """Récupère le dernier score calculé pour un prospect"""
        result = await self.session.execute(
            select(PredictiveScore)
            .where(PredictiveScore.prospect_id == prospect_id)
            .order_by(PredictiveScore.date_calcul.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    async def get_by_category(self, category: str, limit: int = 50) -> List[PredictiveScore]:
        """Récupère les scores par catégorie (HOT, WARM, COLD)"""
        result = await self.session.execute(
            select(PredictiveScore)
            .where(PredictiveScore.categorie == category.upper())
            .order_by(PredictiveScore.score_global.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_hot_leads(self, limit: int = 20) -> List[PredictiveScore]:
        """Récupère les leads HOT prioritaires"""
        return await self.get_by_category("HOT", limit)
    
    async def create_or_update(
        self,
        prospect_id: int,
        score_data: Dict[str, Any]
    ) -> PredictiveScore:
        """Crée ou met à jour un score pour un prospect"""
        new_score = PredictiveScore(
            prospect_id=prospect_id,
            **score_data,
            date_calcul=datetime.utcnow()
        )
        self.session.add(new_score)
        await self.session.commit()
        await self.session.refresh(new_score)
        return new_score


class InteractionRepository(BaseRepository):
    """Repository pour les interactions"""
    
    async def get_by_prospect(self, prospect_id: int, limit: int = 50) -> List[Interaction]:
        """Récupère l'historique des interactions d'un prospect"""
        result = await self.session.execute(
            select(Interaction)
            .where(Interaction.prospect_id == prospect_id)
            .order_by(Interaction.date_interaction.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_by_type(
        self,
        type_interaction: str,
        limit: int = 100
    ) -> List[Interaction]:
        """Récupère les interactions par type"""
        result = await self.session.execute(
            select(Interaction)
            .where(Interaction.type_interaction == type_interaction)
            .order_by(Interaction.date_interaction.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_pending_followups(self) -> List[Interaction]:
        """Récupère les interactions nécessitant un follow-up"""
        result = await self.session.execute(
            select(Interaction)
            .where(
                (Interaction.statut == "opened") &
                (Interaction.date_reponse == None)
            )
            .order_by(Interaction.date_ouverture.asc())
        )
        return list(result.scalars().all())


class OutreachSequenceRepository(BaseRepository):
    """Repository pour les séquences d'outreach"""
    
    async def get_by_prospect(self, prospect_id: int) -> List[OutreachSequence]:
        """Récupère toutes les séquences d'un prospect"""
        result = await self.session.execute(
            select(OutreachSequence)
            .where(OutreachSequence.prospect_id == prospect_id)
            .order_by(OutreachSequence.date_creation.desc())
        )
        return list(result.scalars().all())
    
    async def get_active_sequences(self, limit: int = 50) -> List[OutreachSequence]:
        """Récupère les séquences en cours d'exécution"""
        result = await self.session.execute(
            select(OutreachSequence)
            .where(OutreachSequence.statut == "running")
            .order_by(OutreachSequence.date_debut.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_pending_sequences(self, limit: int = 50) -> List[OutreachSequence]:
        """Récupère les séquences en attente de démarrage"""
        result = await self.session.execute(
            select(OutreachSequence)
            .where(OutreachSequence.statut == "pending")
            .order_by(OutreachSequence.date_creation.asc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def update_step(
        self,
        sequence_id: int,
        new_step: int,
        statut: Optional[str] = None
    ) -> Optional[OutreachSequence]:
        """Met à jour l'étape actuelle d'une séquence"""
        sequence = await self.get_by_id(OutreachSequence, sequence_id)
        
        if sequence:
            sequence.etape_actuelle = new_step
            if statut:
                sequence.statut = statut
            await self.session.commit()
            await self.session.refresh(sequence)
        
        return sequence


def get_repository_factory(session: AsyncSession):
    """
    Factory pour obtenir tous les repositories
    Usage: repos = get_repository_factory(db_session)
           prospects = repos.prospects.get_all()
    """
    class RepositoryFactory:
        def __init__(self, session: AsyncSession):
            self.prospects = ProspectRepository(session)
            self.audits = DigitalAuditRepository(session)
            self.angles = CommercialAngleRepository(session)
            self.interactions = InteractionRepository(session)
            self.scores = PredictiveScoreRepository(session)
            self.sequences = OutreachSequenceRepository(session)
    
    return RepositoryFactory(session)
