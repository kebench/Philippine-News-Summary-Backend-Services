import asyncio
import os
import re
import jmespath
import httpx
from shared.utils.logger import get_logger

logger = get_logger(__name__)


def resolve_env_vars(headers: dict) -> dict:
    """
    Replace ${ENV_VAR} placeholders in header values with actual env var values.
    Keeps secrets out of sources.yaml and in .env where they belong.
    Example: "Bearer ${SOME_API_TOKEN}" → "Bearer actual-token-value"
    """
    resolved = {}
    for key, value in headers.items():
        # Find all ${VAR_NAME} patterns and replace with env var values
        def replace_var(match):
            env_key = match.group(1)
            env_val = os.getenv(env_key)
            if not env_val:
                logger.warning(f"Env var '{env_key}' referenced in headers but not set")
            return env_val or ""
        resolved[key] = re.sub(r"\$\{(\w+)\}", replace_var, value)
    return resolved


async def fetch_all_apis(sources: list[dict]) -> dict:
    """
    Fetch all API sources in parallel.
    Single request per source — no pagination to avoid overburdening the API.
    """
    # Filter only API sources from the full sources list
    api_sources = [s for s in sources if s["type"] == "api"]

    if not api_sources:
        logger.info("No API sources configured")
        return {}

    logger.info(f"Fetching {len(api_sources)} API source(s) in parallel")

    # Run all API fetches concurrently
    tasks = [fetch_api(source) for source in api_sources]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Zip sources and results, log any failures
    output = {}
    for source, result in zip(api_sources, results):
        if isinstance(result, Exception):
            logger.error(f"[{source['name']}] API fetch failed: {result}")
            output[source["name"]] = []
        else:
            logger.info(f"[{source['name']}] Fetched {len(result)} headline(s) from API")
            output[source["name"]] = result

    return output


async def fetch_api(source: dict) -> list[dict]:
    """
    Fetch and parse a single API source.
    Uses JMESPath selectors from sources.yaml to extract headline and article URL.
    Supports optional headers with env var references for auth keys.
    """
    logger.info(f"[{source['name']}] Fetching API from {source['url']}")

    # Resolve headers from sources.yaml — replaces ${ENV_VAR} with actual values
    # Merges with default User-Agent, source headers take precedence
    headers = {
        "User-Agent": "Mozilla/5.0",
        **resolve_env_vars(source.get("headers", {}))
    }

    # Use httpx for async HTTP requests
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(source["url"], headers=headers)
        response.raise_for_status()

    data = response.json()

    # Pull JMESPath selectors from sources.yaml — different APIs have different structures
    # e.g. "listItem[].title" extracts the title field from each item in listItem array
    headline_selector = source["selectors"]["headline"]
    url_selector = source["selectors"]["url"]

    # Extract headlines and URLs using JMESPath — handles nested JSON structures cleanly
    headlines_raw = jmespath.search(headline_selector, data) or []
    urls_raw = jmespath.search(url_selector, data) or []

    # Zip headlines and URLs together — skip entries missing either
    headlines = []
    for headline, article_url in zip(headlines_raw, urls_raw):
        headline = str(headline).strip() if headline else ""
        article_url = str(article_url).strip() if article_url else ""

        # Skip entries missing either a headline or a URL
        if not headline or not article_url:
            logger.debug(f"[{source['name']}] Skipping entry — missing headline or URL")
            continue

        headlines.append({
            "headline": headline,
            "article_url": article_url,
        })

    logger.info(f"[{source['name']}] Parsed {len(headlines)} headline(s) from API response")
    return headlines