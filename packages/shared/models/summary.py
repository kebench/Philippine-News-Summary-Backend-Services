from datetime import datetime
from typing import Optional
from beanie import Document, Link
from pydantic import Field

from .headline import Headline


class Summary(Document):
    date: datetime                        # the news date this summary covers
    headlines: list[str]                  # headline text used as input
    headline_ids: list[str]               # ObjectId refs to raw_headlines
    summary: str
    model_used: str = "unknown"
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "processed_summaries"
        indexes = [
            "date",
            "generated_at",
        ]