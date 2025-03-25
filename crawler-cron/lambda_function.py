import json
import datetime
import asyncio
from functions.utils import read_news, crawl_news_websites, extract_relevant_data, process_news_data

# import sys

# # Ensure UTF-8 output
# sys.stdout.reconfigure(encoding='utf-8')

def lambda_handler(event, context):
	# Open and read the JSON file
	crawled_data = asyncio.run(async_handler())

	print(crawled_data)
	
	return {
		'statusCode': 200,
		'body': json.dumps({'message': f'Cron job executed successfully at {datetime.datetime.now()}'}),
	}

async def async_handler():
	news_websites = read_news()
	crawled_data = await crawl_news_websites(news_websites)
	json_serializable_data = extract_relevant_data(crawled_data)

	
	news_data = process_news_data(json_serializable_data)

	return news_data