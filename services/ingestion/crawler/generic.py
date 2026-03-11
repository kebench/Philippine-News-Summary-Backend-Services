import asyncio
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Browser, BrowserContext

from shared.utils.logger import get_logger

logger = get_logger(__name__)


async def crawl_all(sources: list[dict]) -> dict:
    """
    Launch a single browser instance and crawl all sources in parallel.
    Each source gets its own page (tab), so they run concurrently.
    """
    logger.info(f"Starting parallel crawl for {len(sources)} source(s)")

    async with async_playwright() as p:
        # One shared browser for all sources — much cheaper than one browser per source
        browser = await p.chromium.launch(headless=True)

        # Create a shared browser context with a real user agent —
        # prevents bot detection on sites like PhilStar that block default headless UA
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        # Kick off all crawls at the same time
        tasks = [crawl_source(context, source) for source in sources]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        await browser.close()

    # Log any sources that failed
    output = {}
    for source, result in zip(sources, results):
        if isinstance(result, Exception):
            logger.error(f"[{source['name']}] Crawl failed: {result}")
            output[source["name"]] = []
        else:
            logger.info(f"[{source['name']}] Crawl succeeded — {len(result)} headline(s) found")
            output[source["name"]] = result

    return output


async def crawl_source(context: BrowserContext, source: dict) -> list[str]:
    """
    Crawl a single news source and return a list of headline strings.
    Opens a new page (tab) in the shared browser, handles the cookie banner,
    scrolls to trigger lazy loading, then extracts headlines using the CSS
    selectors defined in sources.yaml.
    """
    logger.info(f"[{source['name']}] Crawling {source['url']}")

    # Each source gets its own tab — this is what enables parallelism
    page = await context.new_page()

    try:
        wait_until = source.get("wait_until", "networkidle")
        # Wait for network to go idle so JS-rendered content is loaded
        await page.goto(source["url"], wait_until=wait_until)

        # Try to dismiss the cookie/privacy banner if it exists
        # Timeout quickly — not all sources will have one
        
        for consent_text in ["I AGREE", "Consent", "Accept", "I Accept", "Agree"]:
            try:
                logger.debug(f"[{source['name']}] Looking for consent button with text '{consent_text}'")
                await page.click(f"text={consent_text}", timeout=3000)
                await page.wait_for_timeout(2000)
                logger.debug(f"[{source['name']}] Dismissed consent banner via '{consent_text}'")
                await page.wait_for_timeout(2000)  # Let the page settle after click
                break  # Stop once one succeeds
            except Exception:
                logger.debug(f"[{source['name']}] No '{consent_text}' button found for consent banner")
                continue

        # Scroll down incrementally to trigger lazy-loaded content
        await scroll_to_bottom(page, source["name"], max_scrolls=source.get("max_scrolls", 10), scroll_wait=source.get("scroll_wait", 500))

        # Grab the fully rendered HTML — classes and IDs are intact here,
        # unlike crawl4ai's cleaned_html which strips them
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")

        # Pull selectors from sources.yaml config — supports a single selector
        # string or a list of selectors targeting different sections of the page
        selectors = source["selectors"]["headline"]
        if isinstance(selectors, str):
            selectors = [selectors]

        # Run each selector and collect all matching headlines
        headlines = []
        # Join all selectors into a single CSS query — one pass, no nesting
        combined_selector = ", ".join(selectors)
        for el in soup.select(combined_selector):
            text = el.get_text(strip=True)
            
            # The <a> tag can be in 3 positions relative to the matched element:
            # 1. The element itself is an <a> tag
            # 2. The <a> tag is a parent wrapping the element
            # 3. The <a> tag is a child inside the element
            a_tag = (
                el if el.name == "a"
                else el.find_parent("a")
                or el.find("a")
            )
            article_url = a_tag.get("href", "") if a_tag else ""
            
            # Skip if no text or no article URL found
            if text and article_url:
                headlines.append({
                    "headline": text,
                    "article_url": article_url,
                })

        return headlines

    finally:
        # Always close the page even if something blows up
        await page.close()


async def scroll_to_bottom(page, source_name: str, max_scrolls: int = 10, scroll_wait: int = 500):
    """
    Incrementally scroll to the bottom of the page to trigger lazy-loaded content.
    Stops early if the page height stops growing or max_scrolls is reached.
    max_scrolls prevents infinite scrolling on sites that load indefinitely.
    scroll_wait specifies the wait time in milliseconds between scrolls.
    """
    logger.debug(f"[{source_name}] Starting scroll to trigger lazy loading")

    last_height = await page.evaluate("document.body.scrollHeight")
    scrolls = 0

    while scrolls < max_scrolls:
        await page.evaluate(f"window.scrollBy(0, {last_height})")
        await page.wait_for_timeout(scroll_wait)  # Wait for new content to load

        new_height = await page.evaluate("document.body.scrollHeight")

        if new_height == last_height:
            logger.debug(f"[{source_name}] Reached bottom of page after {scrolls} scroll(s)")
            break

        last_height = new_height
        scrolls += 1

    # Scroll back to top so the page is in a clean state
    await page.evaluate("window.scrollTo(0, 0)")