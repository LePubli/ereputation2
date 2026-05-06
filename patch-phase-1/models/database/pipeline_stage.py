"""
PipelineStage model for B2B Prospector.
"""
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from .base import Base


class PipelineStage(Base):
    """Pipeline stage model for Kanban board."""
    __tablename__ = "pipeline_stages"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(String(255), nullable=True)
    order = Column(Integer, default=0)
    color = Column(String(20), default="#6B7280")  # Tailwind gray-500
    is_active = Column(Boolean, default=True)
    
    # Relations
    prospects = relationship("Prospect", back_populates="stage")

    def __repr__(self):
        return f"<PipelineStage(id={self.id}, name='{self.name}', order={self.order})>"
