"""
PluginState model for tracking plugin activation status.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON
from datetime import datetime
from .base import Base


class PluginState(Base):
    """Plugin state model for tracking plugin status."""
    __tablename__ = "plugin_states"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    display_name = Column(String(255), nullable=True)
    version = Column(String(20), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=False)
    is_installed = Column(Boolean, default=True)
    last_error = Column(String(500), nullable=True)
    
    # Configuration
    config = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_activated_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<PluginState(id={self.id}, name='{self.name}', active={self.is_active})>"
