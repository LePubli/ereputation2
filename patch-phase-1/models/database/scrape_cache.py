"""
ScrapeCache model for caching scraper results.
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from datetime import datetime, timedelta
from .base import Base


class ScrapeCache(Base):
    """Scrape cache model for storing cached scraper results."""
    __tablename__ = "scrape_cache"

    id = Column(Integer, primary_key=True, index=True)
    
    # Source info
    source = Column(String(50), nullable=False)  # insee, pappers, bodacc, etc.
    query = Column(String(500), nullable=False)  # SIRET, SIREN, company name, etc.
    query_hash = Column(String(64), index=True)  # SHA256 of source+query
    
    # Cached data
    response_data = Column(JSON, default=dict)
    raw_html = Column(Text, nullable=True)
    
    # Cache metadata
    status_code = Column(Integer, default=200)
    error_message = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
    
    @classmethod
    def get_expiry(cls, hours: int = 24) -> datetime:
        """Get expiry datetime."""
        return datetime.utcnow() + timedelta(hours=hours)

    def __repr__(self):
        return f"<ScrapeCache(id={self.id}, source='{self.source}', query='{self.query}')>"
