"""
Scrapers Package - Services de scraping multi-sources
"""
from .base import BaseScraper, ScraperError
from .insee import InseeScraper
from .bodacc import BodaccScraper
from .pappers import PappersScraper
from .pages_jaunes import PagesJaunesScraper
from .google_maps import GoogleMapsScraper
from .aggregator import ScraperAggregator

__all__ = [
    'BaseScraper',
    'ScraperError',
    'InseeScraper',
    'BodaccScraper',
    'PappersScraper',
    'PagesJaunesScraper',
    'GoogleMapsScraper',
    'ScraperAggregator'
]
