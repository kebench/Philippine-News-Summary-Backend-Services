from datetime import datetime
from typing import Optional
from beanie import Document
from pydantic import Field, HttpUrl


class Headline(Document):
    source: str                          # e.g. "rappler", "inquirer", "gma"
    url: str
    headline: str
    snippet: Optional[str] = None
    published_at: Optional[datetime] = None
    crawled_at: datetime = Field(default_factory=datetime.utcnow)
    processed: bool = False              # flipped to True after summarization

    class Settings:
        name = "raw_headlines"
        indexes = [
            "source",
            "processed",
            "published_at",
            [("url", 1)],               # unique index defined in mongo_client
        ]