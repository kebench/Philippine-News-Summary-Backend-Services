import json
import datetime
import asyncio
from functions.utils import read_news, crawl_news_websites, extract_relevant_data

def lambda_handler(event, context):
	now = datetime.datetime.utcnow().isoformat()
	# Open and read the JSON file
	crawled_data = asyncio.run(async_handler())

	return {
		'statusCode': 200,
		'body': json.dumps({'message': f'Cron job executed at {now}'}),
	}

async def async_handler():
	news_websites = read_news()
	crawled_data = await crawl_news_websites(news_websites)
	json_serializable_data = extract_relevant_data(crawled_data)

	return json_serializable_data