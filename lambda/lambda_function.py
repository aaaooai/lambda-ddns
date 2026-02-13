import json
import boto3
import os

route53 = boto3.client('route53')

def lambda_handler(event, context):
    client_ip = event['requestContext']['http']['sourceIp']
    
    headers = event.get('headers', {})
    token = headers.get('authorization')
    
    expected_token = os.environ.get('AUTH_TOKEN')
    if token != f"Bearer {expected_token}":
        return {
            'statusCode': 401,
            'body': json.dumps({'error': 'Unauthorized'})
        }
    
    query_params = event.get('queryStringParameters', {})
    if not query_params or 'record_name' not in query_params:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'record_name parameter is required'})
        }
    
    record_name = query_params['record_name']
    
    allowed_records = os.environ.get('ALLOWED_RECORDS', '').split(',')
    if record_name not in allowed_records:
        return {
            'statusCode': 403,
            'body': json.dumps({'error': 'Record name not allowed'})
        }
    
    hosted_zone_id = os.environ.get('HOSTED_ZONE_ID')
    
    try:
        response = route53.change_resource_record_sets(
            HostedZoneId=hosted_zone_id,
            ChangeBatch={
                'Changes': [{
                    'Action': 'UPSERT',
                    'ResourceRecordSet': {
                        'Name': record_name,
                        'Type': 'A',
                        'TTL': 300,
                        'ResourceRecords': [{'Value': client_ip}]
                    }
                }]
            }
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'ip': client_ip,
                'record': record_name,
                'status': 'updated'
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

