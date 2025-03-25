import json
import datetime

# import sys

# # Ensure UTF-8 output
# sys.stdout.reconfigure(encoding='utf-8')

def lambda_handler(event, context):
  print("Hello World")

  return {
		'statusCode': 200,
		'body': json.dumps({'message': f'Cron job executed successfully at {datetime.datetime.now()}'}),
	}