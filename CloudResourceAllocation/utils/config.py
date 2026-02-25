"""
Configuration file for cloud resource allocation game
Contains constants for resources, tasks, and constraints
"""

# Student ID placeholder (last 2 digits)
STUDENT_ID_LAST_TWO = 88  # Updated with student ID

# Resource prices (p vector)
RESOURCE_PRICES = [1.0, 1.2, 1.5, 1.8, 2.0]

# Number of resources
NUM_RESOURCES = 5

# Execution time matrix (t̂_ij) - time for resource Rj to complete one subtask of task Si
# Rows: Tasks (S1, S2, S3), Columns: Resources (R1, R2, R3, R4, R5)
EXECUTION_TIME_MATRIX = [
    [5.0, 4.2, 3.6, 3.0, 2.8],    # S1
    [6.0, 5.0, 4.0, 3.5, 3.0],    # S2
    [4.0, 3.5, 3.2, 2.8, 2.4]     # S3
]

# Number of subtasks for each task
NUM_SUBTASKS = {
    'S1': 2,
    'S2': 3,
    'S3': 4
}

# Task constraints (deadline in seconds, budget in euros)
TASK_CONSTRAINTS = {
    'S1': {'deadline': 500, 'budget': 20},
    'S2': {'deadline': 300, 'budget': 30},
    'S3': {'deadline': 800, 'budget': 30}
}

# Calculate weights based on student ID
D = STUDENT_ID_LAST_TWO

# Weight for execution time (wt) for each task
WEIGHTS_TIME = {
    'S1': D / 100.0,
    'S2': ((D + 1) % 100) / 100.0,
    'S3': ((D + 2) % 100) / 100.0
}

# Weight for expense (we) for each task
WEIGHTS_EXPENSE = {
    'S1': 1 - WEIGHTS_TIME['S1'],
    'S2': 1 - WEIGHTS_TIME['S2'],
    'S3': 1 - WEIGHTS_TIME['S3']
}

# User ID mapping
USER_IDS = ['S1', 'S2', 'S3']

# AWS Configuration (filled with deployed AWS resources)
AWS_CONFIG = {
    'sqs_queue_url': 'https://sqs.us-east-1.amazonaws.com/210058569281/SubmissionsQueue',
    'dynamodb_table_name': 'ResourceAllocations',
    'region': 'us-east-1',
    'resource_manager_url': 'http://52.207.250.246:5001',
    'user_urls': {
        'S1': 'http://18.207.117.128:5000',
        'S2': 'http://50.19.166.35:5000',
        'S3': 'http://98.80.12.101:5000'
    }
}

def get_user_index(user_id):
    """Get numeric index for user (0, 1, or 2)"""
    return USER_IDS.index(user_id)

def get_execution_times(user_id):
    """Get execution time vector for a specific user"""
    idx = get_user_index(user_id)
    return EXECUTION_TIME_MATRIX[idx]

def print_config():
    """Print configuration for verification"""
    print("=== Cloud Resource Allocation Configuration ===")
    print(f"\nStudent ID (last 2 digits): {STUDENT_ID_LAST_TWO}")
    print(f"\nResource Prices: {RESOURCE_PRICES}")
    print(f"\nExecution Time Matrix:")
    for i, user_id in enumerate(USER_IDS):
        print(f"  {user_id}: {EXECUTION_TIME_MATRIX[i]}")
    print(f"\nNumber of Subtasks:")
    for user_id in USER_IDS:
        print(f"  {user_id}: {NUM_SUBTASKS[user_id]}")
    print(f"\nWeights (Time, Expense):")
    for user_id in USER_IDS:
        print(f"  {user_id}: wt={WEIGHTS_TIME[user_id]:.2f}, we={WEIGHTS_EXPENSE[user_id]:.2f}")
    print(f"\nConstraints (Deadline, Budget):")
    for user_id in USER_IDS:
        c = TASK_CONSTRAINTS[user_id]
        print(f"  {user_id}: T={c['deadline']}s, M={c['budget']}€")

if __name__ == '__main__':
    print_config()

