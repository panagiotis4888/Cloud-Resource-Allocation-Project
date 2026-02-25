"""
Lambda Function 2: Get and Send
Retrieves allocations from DynamoDB and sends to Resource Manager
"""

import json
import boto3
import os
import urllib.request
import urllib.error
from datetime import datetime
from decimal import Decimal

# Environment variables
DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE', 'ResourceAllocations')
RESOURCE_MANAGER_URL = os.environ.get('RESOURCE_MANAGER_URL', '')
REGION = os.environ.get('AWS_REGION', 'us-east-1')

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb', region_name=REGION)
table = dynamodb.Table(DYNAMODB_TABLE)

USER_IDS = ['S1', 'S2', 'S3']


def lambda_handler(event, context):
    """
    Retrieve allocations from DynamoDB and send to Resource Manager
    
    Event structure:
    {
        "step": 1,
        "trigger_source": "submission_handler" or "manual"
    }
    """
    print(f"Received event: {json.dumps(event)}")
    
    step = event.get('step', 1)
    
    try:
        # Retrieve allocations from DynamoDB
        allocations, timestamps = get_pending_allocations(step)
        
        if len(allocations) != len(USER_IDS):
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': f'Expected {len(USER_IDS)} allocations, got {len(allocations)}',
                    'allocations': allocations
                })
            }
        
        print(f"Retrieved allocations for step {step}: {list(allocations.keys())}")
        
        # Send to Resource Manager
        if RESOURCE_MANAGER_URL:
            response = send_to_resource_manager(allocations, step)
            
            # Update status in DynamoDB
            update_allocation_status(allocations, timestamps, 'processed')
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': f'Successfully processed step {step}',
                    'allocations': allocations,
                    'resource_manager_response': response
                })
            }
        else:
            print("WARNING: RESOURCE_MANAGER_URL not configured")
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'Retrieved allocations but Resource Manager URL not configured',
                    'allocations': allocations
                })
            }
        
    except Exception as e:
        print(f"Error in lambda_handler: {e}")
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def get_pending_allocations(step):
    """
    Retrieve pending allocations from DynamoDB for given step
    
    Args:
        step: Step number
    
    Returns:
        Tuple of (allocations_dict, timestamps_dict) where:
        - allocations_dict: Dictionary mapping user_id to allocation_vector
        - timestamps_dict: Dictionary mapping user_id to timestamp
    """
    allocations = {}
    timestamps = {}
    
    for user_id in USER_IDS:
        try:
            # Query for most recent pending submission by this user for this step
            response = table.query(
                KeyConditionExpression=boto3.dynamodb.conditions.Key('user_id').eq(user_id),
                FilterExpression=boto3.dynamodb.conditions.Attr('step').eq(step) & 
                               boto3.dynamodb.conditions.Attr('status').eq('pending'),
                ScanIndexForward=False,  # Most recent first
                Limit=1
            )
            
            if response['Items']:
                item = response['Items'][0]
                # Convert Decimal values to int for JSON serialization
                allocation_vector = item['allocation_vector']
                allocations[user_id] = [int(v) for v in allocation_vector]
                timestamps[user_id] = item['timestamp']
                print(f"Found allocation for {user_id}: {allocations[user_id]}")
            else:
                print(f"WARNING: No pending allocation found for {user_id} in step {step}")
        
        except Exception as e:
            print(f"Error retrieving allocation for {user_id}: {e}")
    
    return allocations, timestamps


def send_to_resource_manager(allocations, step):
    """
    Send allocations to Resource Manager EC2
    
    Args:
        allocations: Dictionary of user_id -> allocation_vector
        step: Step number
    
    Returns:
        Response from Resource Manager
    """
    try:
        payload = {
            'allocations': allocations,
            'step': step
        }
        
        # Ensure no double slashes in URL
        base_url = RESOURCE_MANAGER_URL.rstrip('/')
        url = f"{base_url}/calculate_matrices"
        
        print(f"Sending to Resource Manager: {url}")
        print(f"Payload: {json.dumps(payload)}")
        
        # Prepare request data
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            url,
            data=data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        
        # Send request with timeout
        # urlopen automatically raises HTTPError for 4xx/5xx status codes
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                status_code = response.getcode()
                response_data = response.read().decode('utf-8')
                result = json.loads(response_data)
                print(f"Resource Manager response: {status_code}")
                return result
        except urllib.error.HTTPError as e:
            # HTTP error (4xx, 5xx)
            error_body = e.read().decode('utf-8') if e.fp else str(e)
            print(f"HTTP Error {e.code}: {error_body}")
            raise
        
    except Exception as e:
        print(f"Error sending to Resource Manager: {e}")
        raise


def update_allocation_status(allocations, timestamps, new_status):
    """
    Update status of allocations in DynamoDB
    
    Args:
        allocations: Dictionary of allocations (keys are user_ids)
        timestamps: Dictionary of timestamps (keys are user_ids)
        new_status: New status value (e.g., 'processed')
    """
    for user_id in allocations.keys():
        try:
            if user_id not in timestamps:
                print(f"WARNING: No timestamp found for {user_id}, skipping status update")
                continue
            
            # Update using both partition key (user_id) and sort key (timestamp)
            response = table.update_item(
                Key={
                    'user_id': user_id,
                    'timestamp': timestamps[user_id]
                },
                UpdateExpression='SET #status = :status',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={':status': new_status}
            )
            print(f"Updated status for {user_id} to {new_status}")
        except Exception as e:
            print(f"Error updating status for {user_id}: {e}")


# For local testing
if __name__ == '__main__':
    # Mock event
    test_event = {
        'step': 1,
        'trigger_source': 'manual'
    }
    
    result = lambda_handler(test_event, None)
    print(f"Result: {json.dumps(result, indent=2)}")

