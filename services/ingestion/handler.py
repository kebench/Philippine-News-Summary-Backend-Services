"""
Lambda handler for the ingestion service.
Triggered by EventBridge cron — crawls PH news sources and calls NewsAPI,
then saves raw headlines to MongoDB.
"""
import asyncio

from shared.db import init_db, close_db
from shared.utils import get_logger


logger = get_logger(__name__)



async def run() -> dict:
    await init_db()

    results = {"crawled": 0, "api": 0, "errors": []}

    try:
        print("Crawling sources...")
        
        # TODO: Implement crawling logic here.
    except Exception as e:
        logger.error(f"NewsAPI failed: {e}")
        results["errors"].append(str(e))

    finally:
        await close_db()

    logger.info(f"Ingestion complete: {results}")
    return results


def handler(event: dict, context) -> dict:
    """AWS Lambda entrypoint."""
    return asyncio.run(run())


if __name__ == "__main__":
    # Local dev entrypoint
    asyncio.run(run())