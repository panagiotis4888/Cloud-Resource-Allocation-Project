"""
Lambda Function 1: Submission Handler
Triggered by SQS messages, stores allocations in DynamoDB
When all 3 users have submitted, triggers Lambda 2
"""

import json
import boto3
import os
from datetime import datetime

# Environment variables (set in Lambda configuration)
DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE', 'ResourceAllocations')
LAMBDA_FUNCTION_2 = os.environ.get('LAMBDA_FUNCTION_2', 'get-and-send')
REGION = os.environ.get('AWS_REGION', 'us-east-1')

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb', region_name=REGION)
lambda_client = boto3.client('lambda', region_name=REGION)
table = dynamodb.Table(DYNAMODB_TABLE)

USER_IDS = ['S1', 'S2', 'S3']


def lambda_handler(event, context):
    """
    Handle SQS message containing user allocation
    
    Event structure:
    {
        "Records": [
            {
                "body": "{\"user_id\": \"S1\", \"allocation_vector\": [0,0,0,1,1], ...}"
            }
        ]
    }
    """
    print(f"Received event: {json.dumps(event)}")
    
    processed_count = 0
    
    # Process each SQS record
    for record in event['Records']:
        try:
            # Parse message body
            message = json.loads(record['body'])
            
            user_id = message['user_id']
            allocation_vector = message['allocation_vector']
            expected_utility = message['expected_utility']
            timestamp = message.get('timestamp', datetime.utcnow().isoformat())
            step = message.get('step', 1)
            
            print(f"Processing allocation for {user_id}, step {step}")
            
            # Store in DynamoDB
            item = {
                'user_id': user_id,
                'timestamp': timestamp,
                'allocation_vector': allocation_vector,
                'expected_utility': expected_utility,
                'step': step,
                'status': 'pending'
            }
            
            table.put_item(Item=item)
            print(f"Stored allocation for {user_id} in DynamoDB")
            
            processed_count += 1
            
            # Check if all users have submitted for this step
            if check_all_users_submitted(step):
                print(f"All users submitted for step {step}, triggering Lambda 2")
                trigger_lambda_2(step)
            
        except Exception as e:
            print(f"Error processing record: {e}")
            # Continue processing other records
            continue
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': f'Processed {processed_count} allocations',
            'processed': processed_count
        })
    }


def check_all_users_submitted(step):
    """
    Check if all 3 users have submitted allocations for given step
    
    Args:
        step: Step number to check
    
    Returns:
        True if all users have submitted, False otherwise
    """
    try:
        submitted_users = set()
        
        for user_id in USER_IDS:
            # Query for most recent submission by this user for this step
            response = table.query(
                KeyConditionExpression=boto3.dynamodb.conditions.Key('user_id').eq(user_id),
                FilterExpression=boto3.dynamodb.conditions.Attr('step').eq(step) & 
                               boto3.dynamodb.conditions.Attr('status').eq('pending'),
                ScanIndexForward=False,  # Most recent first
                Limit=1
            )
            
            if response['Items']:
                submitted_users.add(user_id)
        
        all_submitted = len(submitted_users) == len(USER_IDS)
        print(f"Step {step} - Submitted: {submitted_users}, All submitted: {all_submitted}")
        
        return all_submitted
        
    except Exception as e:
        print(f"Error checking submissions: {e}")
        return False


def trigger_lambda_2(step):
    """
    Trigger Lambda Function 2 (Get and Send)
    
    Args:
        step: Step number to process
    """
    try:
        payload = {
            'step': step,
            'trigger_source': 'submission_handler'
        }
        
        response = lambda_client.invoke(
            FunctionName=LAMBDA_FUNCTION_2,
            InvocationType='Event',  # Asynchronous invocation
            Payload=json.dumps(payload)
        )
        
        print(f"Triggered Lambda 2: {response['StatusCode']}")
        return response
        
    except Exception as e:
        print(f"Error triggering Lambda 2: {e}")
        raise


# For local testing
if __name__ == '__main__':
    # Mock SQS event
    test_event = {
        'Records': [
            {
                'body': json.dumps({
                    'user_id': 'S1',
                    'allocation_vector': [0, 0, 0, 1, 1],
                    'expected_utility': 0.0633,
                    'timestamp': datetime.utcnow().isoformat(),
                    'step': 1
                })
            }
        ]
    }
    
    result = lambda_handler(test_event, None)
    print(f"Result: {json.dumps(result, indent=2)}")

