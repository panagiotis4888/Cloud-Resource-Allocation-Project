"""
Flask application for Resource Manager EC2
Receives allocations, calculates matrices, and sends results to users
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, jsonify
import requests
from provider.resource_manager import ResourceManager
from utils.config import AWS_CONFIG, USER_IDS

app = Flask(__name__)

# Initialize Resource Manager
manager = ResourceManager()

# Store state
state = {
    'step': 0,
    'allocations': {},
    'results': None,
    'step1_time_matrix': None  # Store for Step 2 calculation
}


def send_matrices_to_users(results, step):
    """
    Send T and E matrices to all users
    
    Args:
        results: Results from ResourceManager.process_allocations()
        step: Step number (1 or 2)
    
    Returns:
        Dictionary of responses from users
    """
    responses = {}
    
    for user_id in USER_IDS:
        user_url = AWS_CONFIG['user_urls'].get(user_id)
        
        if not user_url:
            print(f"WARNING: URL not configured for {user_id}")
            continue
        
        try:
            user_result = results['user_results'][user_id]
            
            payload = {
                'time_vector': user_result['time_vector'],
                'expense_vector': user_result['expense_vector'],
                'step': step
            }
            
            response = requests.post(
                f"{user_url}/receive_matrices",
                json=payload,
                timeout=10
            )
            
            responses[user_id] = response.json()
            print(f"Sent matrices to {user_id}: {response.status_code}")
            
        except Exception as e:
            print(f"Error sending to {user_id}: {e}")
            responses[user_id] = {'error': str(e)}
    
    return responses


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'role': 'resource_manager',
        'step': state['step']
    })


@app.route('/calculate_matrices', methods=['POST'])
def calculate_matrices():
    """
    Receive allocation vectors from all users and calculate matrices
    
    Request body:
    {
        "allocations": {
            "S1": [0, 0, 0, 1, 1],
            "S2": [0, 0, 1, 1, 1],
            "S3": [1, 1, 1, 0, 1]
        },
        "step": 1
    }
    
    Returns:
    {
        "allocation_matrix": [[0,0,0,1,1], [0,0,1,1,1], [1,1,1,0,1]],
        "time_matrix": [...],
        "expense_matrix": [...],
        "user_results": {...},
        "multiplexing": {...}
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        allocations = data.get('allocations')
        step = data.get('step', 1)
        
        if not allocations:
            return jsonify({'error': 'Missing allocations'}), 400
        
        print(f"\n=== Calculate Matrices Request (Step {step}) ===")
        
        # Validate all users present
        missing_users = [uid for uid in USER_IDS if uid not in allocations]
        if missing_users:
            return jsonify({'error': f'Missing allocations for: {missing_users}'}), 400
        
        # Process allocations
        results = manager.process_allocations(allocations)
        multiplexing_info = manager.check_multiplexing(results['allocation_matrix'])
        
        # Store state
        state['allocations'] = allocations
        state['results'] = results
        state['step'] = step
        
        if step == 1:
            state['step1_time_matrix'] = results['time_matrix']
        
        # Send matrices to users if URLs configured
        user_responses = {}
        if any(AWS_CONFIG['user_urls'].values()):
            user_responses = send_matrices_to_users(results, step)
        
        return jsonify({
            'allocation_matrix': results['allocation_matrix'],
            'time_matrix': results['time_matrix'],
            'expense_matrix': results['expense_matrix'],
            'user_results': results['user_results'],
            'multiplexing': multiplexing_info,
            'step': step,
            'user_responses': user_responses
        })
        
    except Exception as e:
        print(f"Error in calculate_matrices: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/prepare_step2', methods=['POST'])
def prepare_step2():
    """
    Calculate updated execution times for Step 2
    
    Uses time matrix from Step 1 to calculate new base execution times
    Formula: t_new_ij = t̂_ij + Σ(tij)/n
    
    Returns:
    {
        "updated_execution_times": {
            "S1": [5.5, 4.7, 4.1, 3.5, 3.3],
            "S2": [6.5, 5.5, 4.5, 4.0, 3.5],
            "S3": [4.5, 4.0, 3.7, 3.3, 2.9]
        },
        "step": 2
    }
    """
    try:
        if not state['step1_time_matrix']:
            return jsonify({'error': 'Step 1 must be completed first'}), 400
        
        print(f"\n=== Preparing Step 2 ===")
        
        # Calculate updated execution times
        updated_times = manager.calculate_step2_execution_times(state['step1_time_matrix'])
        
        # Format as dictionary for each user
        updated_execution_times = {}
        for i, user_id in enumerate(USER_IDS):
            updated_execution_times[user_id] = updated_times[i]
        
        return jsonify({
            'updated_execution_times': updated_execution_times,
            'step': 2,
            'message': 'Send these to users for Step 2 optimization'
        })
        
    except Exception as e:
        print(f"Error in prepare_step2: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/get_results', methods=['GET'])
def get_results():
    """Get complete results"""
    if not state['results']:
        return jsonify({'error': 'No results available yet'}), 404
    
    return jsonify({
        'step': state['step'],
        'allocations': state['allocations'],
        'allocation_matrix': state['results']['allocation_matrix'],
        'time_matrix': state['results']['time_matrix'],
        'expense_matrix': state['results']['expense_matrix'],
        'user_results': state['results']['user_results']
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    print(f"\n{'='*60}")
    print(f"Starting Resource Manager Flask App")
    print(f"Port: {port}")
    print(f"{'='*60}\n")
    
    app.run(host='0.0.0.0', port=port, debug=True)

