import json
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode, BrowserConfig, SemaphoreDispatcher, RateLimiter, LXMLWebScrapingStrategy
import re
from datetime import datetime
# from crawl4ai.extraction_strategy import CosineStrategy

def read_news():
  with open('functions/phil-news-websites.json') as json_file:
    data = json.load(json_file)
  return data


async def crawl_news_websites(urls):
  browser_config = BrowserConfig(headless=True, verbose=False)
  run_config = CrawlerRunConfig(
    scraping_strategy=LXMLWebScrapingStrategy(),
    cache_mode=CacheMode.BYPASS,
    excluded_tags=['form', 'header', 'footer', 'nav'],
    exclude_external_links=True,    
    exclude_social_media_links=True,
    exclude_domains=["adtrackers.com", "spammynews.org"],    
    exclude_social_media_domains=["facebook.com", "twitter.com"],
    remove_overlay_elements=True,
    target_elements=["div.just-in-content", "div#new-channel-grid", "h2.text-2xl", "div.news_title"],
    # js_code="document.querySelector('.fc-cta-consent')?.click();",
    simulate_user=True,
    magic=True,
    scan_full_page=True
  )

  dispatcher = SemaphoreDispatcher(
    semaphore_count=5,
    rate_limiter=RateLimiter(
      base_delay=(0.5, 1.0),
      max_delay=10.0
    )
  )

  async with AsyncWebCrawler(config=browser_config) as crawler:
    results = await crawler.arun_many(
      urls,
      config=run_config,
      dispatcher=dispatcher,
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

def clean_news_headlines(news):
  cleaned_text = re.sub(r'\d{1,2}:\d{2} [APM]{2}', '', news)

	# Extract only the headlines
  headlines = [re.sub(r'\[|\]', '', match) for match in re.findall(r'\[([^\]]+)\]', cleaned_text)]
  return headlines

def process_news_data(crawled_data):
  news_data = []
  current_date = datetime.now().strftime("%Y-%m-%d")
  sources = ["GMA News", "Philippine Daily Inquirer", "PNA GOV PH", "Philippine Star"]
  for index, data in enumerate(crawled_data):
    headlines = clean_news_headlines(data["markdown"])
    
    news_data.extend([{
        "source": sources[index],
        "headline": headline.strip(),
        "date": current_date
    } for headline in headlines])
  return news_data