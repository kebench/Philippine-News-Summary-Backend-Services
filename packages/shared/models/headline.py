from datetime import datetime
from beanie import Document
from pydantic import Field
import hashlib

class Headline(Document):
    headline: str
    source_name: str
    article_url: str
    headline_hash: str                                          # MD5 of article_url — dedup key
    crawled_at: datetime = Field(default_factory=datetime.utcnow)  # Full timestamp
    crawled_date: str = Field(default_factory=lambda: datetime.utcnow().date().isoformat())  # Date only — easy daily queries

    class Settings:
        name = "raw_headlines"
        indexes = [
            "headline_hash",    # Fast dedup lookup
            "crawled_date",     # Summarizer queries by date
            "source_name",      # Filter by source
        ]

    @staticmethod
    def make_hash(article_url: str) -> str:
        """Generate MD5 hash of article_url — used as dedup key on upsert."""
        return hashlib.md5(article_url.encode()).hexdigest()