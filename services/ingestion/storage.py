from datetime import datetime
from beanie import BulkWriter
from beanie.operators import Set
from pymongo import UpdateOne
from shared.models.headline import Headline as RawHeadline
from shared.utils.logger import get_logger

logger = get_logger(__name__)


async def save_headlines(source_name: str, headlines: list[dict]):
    """
    Upsert headlines into MongoDB in bulk using Beanie's native BulkWriter.
    Uses headline_hash as the unique key — if it already exists, skip.
    If it's new, insert it. One DB operation, no separate read needed.
    """
    if not headlines:
        logger.info(f"[{source_name}] No headlines to save")
        return

    now = datetime.utcnow()

    # Build upsert operations for all headlines
    operations = [
        UpdateOne(
            # Match on headline_hash — our dedup key
            {"headline_hash": RawHeadline.make_hash(item["article_url"])},
            # Only set fields on insert — never overwrite existing docs
            {"$setOnInsert": {
                "headline": item["headline"],
                "source_name": source_name,
                "article_url": item["article_url"],
                "headline_hash": RawHeadline.make_hash(item["article_url"]),
                "crawled_at": now,
                "crawled_date": now.date().isoformat(),
            }},
            upsert=True
        )
        for item in headlines
    ]

    # Beanie 2.0 uses get_pymongo_collection() — Motor has been dropped
    result = await RawHeadline.get_pymongo_collection().bulk_write(operations, ordered=False)

    logger.info(f"[{source_name}] Inserted {result.upserted_count} new headline(s), skipped {result.matched_count} duplicate(s)")