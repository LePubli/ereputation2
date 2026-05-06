"""
AuditLog model for tracking user activities.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base


class AuditLog(Base):
    """Audit log model for tracking user activities."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    
    # Action info
    action = Column(String(100), nullable=False)  # create, update, delete, login, etc.
    entity_type = Column(String(50), nullable=False)  # prospect, user, plugin, etc.
    entity_id = Column(Integer, nullable=True)
    
    # User info
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user_email = Column(String(255), nullable=True)
    
    # Details
    description = Column(Text, nullable=True)
    details = Column(JSON, default=dict)
    ip_address = Column(String(45), nullable=True)  # IPv6 max length
    user_agent = Column(String(500), nullable=True)
    
    # Status
    status = Column(String(20), default="success")  # success, error
    error_message = Column(String(500), nullable=True)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relations
    prospect = relationship("Prospect", back_populates="audit_logs")

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action='{self.action}', entity='{self.entity_type}')>"
