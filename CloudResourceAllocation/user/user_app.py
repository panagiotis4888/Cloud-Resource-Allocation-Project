"""
Flask application for User EC2 instances
Handles optimization and communication with Cloud Provider
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, jsonify
import boto3
import json
from datetime import datetime
from user.optimizer import UserOptimizer
from utils.config import AWS_CONFIG

# Get user ID from environment variable or command line
USER_ID = os.environ.get('USER_ID', 'S1')

app = Flask(__name__)

# Initialize optimizer
optimizer = UserOptimizer(USER_ID)

# Store state
state = {
    'allocation_vector': None,
    'expected_utility': None,
    'actual_utility': None,
    'time_vector': None,
    'expense_vector': None,
    'step': 0
}


def send_to_sqs(allocation_vector, expected_utility, step):
    """
    Send allocation vector to SQS queue
    
    Args:
        allocation_vector: Allocation vector to submit
        expected_utility: Expected utility value
        step: Step number (1 or 2)
    """
    sqs_url = AWS_CONFIG['sqs_queue_url']
    
    if not sqs_url:
        print("WARNING: SQS queue URL not configured. Skipping SQS submission.")
        return
    
    try:
        sqs = boto3.client('sqs', region_name=AWS_CONFIG['region'])
        
        message = {
            'user_id': USER_ID,
            'allocation_vector': allocation_vector,
            'expected_utility': expected_utility,
            'timestamp': datetime.utcnow().isoformat(),
            'step': step
        }
        
        response = sqs.send_message(
            QueueUrl=sqs_url,
            MessageBody=json.dumps(message)
        )
        
        print(f"Sent message to SQS: {response['MessageId']}")
        return response
        
    except Exception as e:
        print(f"Error sending to SQS: {e}")
        raise


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'user_id': USER_ID,
        'step': state['step']
    })


@app.route('/optimize', methods=['POST'])
def optimize():
    """
    Trigger optimization for this user
    
    Request body (optional):
    {
        "step": 1 or 2,
        "custom_execution_times": [5.0, 4.2, 3.6, 3.0, 2.8]  // for step 2
    }
    
    Returns:
    {
        "user_id": "S1",
        "allocation_vector": [0, 0, 0, 1, 1],
        "expected_utility": 0.0633,
        "step": 1
    }
    """
    try:
        data = request.get_json() or {}
        step = data.get('step', 1)
        custom_times = data.get('custom_execution_times', None)
        
        print(f"\n=== Optimization Request for {USER_ID} (Step {step}) ===")
        
        # Perform optimization
        allocation, utility = optimizer.optimize_step1(custom_execution_times=custom_times)
        
        # Store state
        state['allocation_vector'] = allocation
        state['expected_utility'] = utility
        state['step'] = step
        
        # Send to SQS if configured
        try:
            if AWS_CONFIG['sqs_queue_url']:
                send_to_sqs(allocation, utility, step)
        except Exception as e:
            print(f"Warning: Could not send to SQS: {e}")
        
        return jsonify({
            'user_id': USER_ID,
            'allocation_vector': allocation,
            'expected_utility': utility,
            'step': step,
            'status': 'submitted'
        })
        
    except Exception as e:
        print(f"Error in optimize: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/receive_matrices', methods=['POST'])
def receive_matrices():
    """
    Receive T and E matrices from Resource Manager
    
    Request body:
    {
        "time_vector": [0, 0, 7.2, 6, 8.4],
        "expense_vector": [0, 0, 5.4, 5.4, 5.6],
        "step": 1
    }
    
    Returns:
    {
        "user_id": "S1",
        "actual_utility": 0.0469,
        "expected_utility": 0.0633,
        "utility_loss": 0.0164
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        time_vector = data.get('time_vector')
        expense_vector = data.get('expense_vector')
        step = data.get('step', state['step'])
        
        if not time_vector or not expense_vector:
            return jsonify({'error': 'Missing time_vector or expense_vector'}), 400
        
        print(f"\n=== Received Matrices for {USER_ID} (Step {step}) ===")
        
        # Calculate actual utility
        actual_utility = optimizer.calculate_actual_utility_from_matrices(
            time_vector, expense_vector
        )
        
        # Store state
        state['time_vector'] = time_vector
        state['expense_vector'] = expense_vector
        state['actual_utility'] = actual_utility
        
        utility_loss = state['expected_utility'] - actual_utility if state['expected_utility'] else 0
        
        return jsonify({
            'user_id': USER_ID,
            'actual_utility': actual_utility,
            'expected_utility': state['expected_utility'],
            'utility_loss': utility_loss,
            'max_time': max(time_vector),
            'total_expense': sum(expense_vector),
            'step': step
        })
        
    except Exception as e:
        print(f"Error in receive_matrices: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/get_allocation', methods=['GET'])
def get_allocation():
    """Get current allocation and state"""
    return jsonify({
        'user_id': USER_ID,
        'allocation_vector': state['allocation_vector'],
        'expected_utility': state['expected_utility'],
        'actual_utility': state['actual_utility'],
        'step': state['step']
    })


@app.route('/get_results', methods=['GET'])
def get_results():
    """Get complete results for reporting"""
    return jsonify({
        'user_id': USER_ID,
        'allocation_vector': state['allocation_vector'],
        'expected_utility': state['expected_utility'],
        'actual_utility': state['actual_utility'],
        'utility_loss': (state['expected_utility'] - state['actual_utility']) 
                       if state['expected_utility'] and state['actual_utility'] else None,
        'max_time': max(state['time_vector']) if state['time_vector'] else None,
        'total_expense': sum(state['expense_vector']) if state['expense_vector'] else None,
        'step': state['step'],
        'constraints': {
            'deadline': optimizer.deadline,
            'budget': optimizer.budget
        },
        'weights': {
            'time': optimizer.weight_time,
            'expense': optimizer.weight_expense
        }
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"\n{'='*60}")
    print(f"Starting User Flask App: {USER_ID}")
    print(f"Port: {port}")
    print(f"{'='*60}\n")
    
    app.run(host='0.0.0.0', port=port, debug=True)

