import json
import datetime

def lambda_handler(event, context):
    now = datetime.datetime.utcnow().isoformat()
    return {
        'statusCode': 200,
        'body': json.dumps(f'Cron job executed at {now}')
    }