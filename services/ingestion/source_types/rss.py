import asyncio
import feedparser
import httpx
from shared.utils.logger import get_logger

logger = get_logger(__name__)


async def fetch_all_rss(sources: list[dict]) -> dict:
    """
    Fetch all RSS sources in parallel.
    RSS is much cheaper than crawling — no browser, no JS, just HTTP + XML.
    """
    # Filter only RSS sources from the full sources list
    rss_sources = [s for s in sources if s["type"] == "rss"]

    if not rss_sources:
        logger.info("No RSS sources configured")
        return {}

    logger.info(f"Fetching {len(rss_sources)} RSS source(s) in parallel")

    # Run all RSS fetches concurrently
    tasks = [fetch_rss(source) for source in rss_sources]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Zip sources and results, log any failures
    output = {}
    for source, result in zip(rss_sources, results):
        if isinstance(result, Exception):
            logger.error(f"[{source['name']}] RSS fetch failed: {result}")
            output[source["name"]] = []
        else:
            logger.info(f"[{source['name']}] Fetched {len(result)} headline(s) from RSS")
            output[source["name"]] = result

    return output


async def fetch_rss(source: dict) -> list[dict]:
    """
    Fetch and parse a single RSS feed.
    Uses selectors from sources.yaml to extract headline and article URL
    since different feeds may store them in different fields.
    """
    logger.info(f"[{source['name']}] Fetching RSS from {source['url']}")

    # Use httpx for async HTTP — no browser needed for RSS
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            source["url"],
            # Mimic a browser user agent — some feeds block default httpx UA
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
        )
        response.raise_for_status()

    # feedparser handles all RSS/Atom variants and malformed XML gracefully
    feed = feedparser.parse(response.text)

    if not feed.entries:
        logger.warning(f"[{source['name']}] RSS feed returned no entries")
        return []

    # Pull selectors from sources.yaml — different feeds use different fields
    # e.g. most use title + link, but some may use description or guid for URL
    headline_field = source["selectors"]["headline"]
    url_field = source["selectors"]["url"]

    # Extract headline and article URL from each feed entry
    headlines = []
    for entry in feed.entries:
        headline = entry.get(headline_field, "").strip()
        article_url = entry.get(url_field, "").strip()

        # Skip entries missing either a headline or a URL
        if not headline or not article_url:
            logger.debug(f"[{source['name']}] Skipping entry — missing '{headline_field}' or '{url_field}'")
            continue

        headlines.append({
            "headline": headline,
            "article_url": article_url,
        })

    logger.info(f"[{source['name']}] Parsed {len(headlines)} headline(s) from RSS feed")
    return headlines