import json
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode, BrowserConfig, SemaphoreDispatcher, RateLimiter, CrawlerMonitor, DisplayMode

def read_news():
  with open('functions/phil-news-websites.json') as json_file:
    data = json.load(json_file)
  return data


async def crawl_news_websites(urls):
  browser_config = BrowserConfig(headless=True, verbose=False)
  run_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)

  dispatcher = SemaphoreDispatcher(
    semaphore_count=5,
    rate_limiter=RateLimiter(
      base_delay=(0.5, 1.0),
      max_delay=10.0
    ),
    monitor=CrawlerMonitor(
      max_visible_rows=15,
      display_mode=DisplayMode.DETAILED
    )
  )

  async with AsyncWebCrawler(config=browser_config) as crawler:
    results = await crawler.arun_many(
      urls, 
      config=run_config,
      dispatcher=dispatcher
    )
  return results

def extract_relevant_data(crawled_results):
  extracted_data = []
  
  for result in crawled_results:
    extracted_data.append({
      "cleaned_html": result.cleaned_html,  # Processed HTML without scripts/styles
      "markdown": result.markdown if isinstance(result.markdown, str) else None,  # Markdown content
      "extracted_content": result.extracted_content,  # Structured extraction
      "media": result.media,  # List of extracted media details
      "links": result.links,  # Internal & external links
    })

  return extracted_data
