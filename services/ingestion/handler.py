"""
Lambda handler for the ingestion service.
Triggered by EventBridge cron — crawls PH news sources and calls external APIs,
then saves raw headlines to MongoDB.
"""
import asyncio
import os

from dotenv import load_dotenv
from shared.db import init_db, close_db
from shared.utils import get_logger
from utils.config_loader import load_sources
from source_types.crawler import crawl_all
from source_types.rss import fetch_all_rss
from source_types.api_caller import fetch_all_apis
from utils.storage import save_headlines

# Local dev only — Lambda injects env vars directly
if not os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
    load_dotenv()

logger = get_logger(__name__)


async def run() -> dict:
    await init_db()

    results = {"fetched": {}, "errors": []}

    try:
        sources = load_sources("sources.yaml")
        logger.info(f"Loaded {len(sources)} sources")

        # Filter sources by type and route to the appropriate handler
        crawl_sources_list = [s for s in sources if s["type"] == "crawl"]
        api_sources_list = [s for s in sources if s["type"] == "api"]
        rss_sources_list = [s for s in sources if s["type"] == "rss"]
        
        # Crawl all crawlable sources in parallel
        if crawl_sources_list:
            logger.info(f"Starting crawl for {len(crawl_sources_list)} source(s)")
            results["fetched"].update(await crawl_all(crawl_sources_list))

        if rss_sources_list:
            logger.info(f"Starting RSS fetch for {len(rss_sources_list)} source(s)")
            results["fetched"].update(await fetch_all_rss(rss_sources_list))

        # Fetch all API sources in parallel — this is separate from crawling since it uses httpx, not Playwright
        if api_sources_list:
            logger.info(f"Starting API fetch for {len(api_sources_list)} source(s)")
            results["fetched"].update(await fetch_all_apis(api_sources_list))

        # Save all fetched headlines to MongoDB
        for source_name, headlines in results["fetched"].items():
            await save_headlines(source_name, headlines)
    
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        results["errors"].append(str(e))

    finally:
        await close_db()

    # logger.info(f"Ingestion complete: {results}")
    return results


def handler(event: dict, context) -> dict:
    """AWS Lambda entrypoint."""
    return asyncio.run(run())


if __name__ == "__main__":
    asyncio.run(run())