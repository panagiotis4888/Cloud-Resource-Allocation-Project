"""
Resource Manager logic for Cloud Provider
Calculates actual execution times and expenses accounting for multiplexing
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.calculations import (
    calculate_actual_execution_matrix,
    calculate_actual_expense_matrix,
    print_matrix
)
from utils.config import (
    EXECUTION_TIME_MATRIX,
    RESOURCE_PRICES,
    USER_IDS
)
from typing import List, Dict, Tuple


class ResourceManager:
    """
    Manages resource allocation and calculates actual execution times/expenses
    """
    
    def __init__(self):
        """Initialize Resource Manager"""
        self.base_execution_times = EXECUTION_TIME_MATRIX
        self.resource_prices = RESOURCE_PRICES
        self.user_ids = USER_IDS
        
        print("\n=== Resource Manager Initialized ===")
        print(f"Managing {len(self.user_ids)} users and {len(self.resource_prices)} resources")
    
    def process_allocations(self, 
                          allocations: Dict[str, List[int]]) -> Dict[str, Dict]:
        """
        Process allocation vectors from all users and calculate matrices
        
        Args:
            allocations: Dictionary mapping user_id to allocation_vector
                        e.g., {'S1': [0,0,0,1,1], 'S2': [0,0,1,1,1], 'S3': [1,1,1,0,1]}
        
        Returns:
            Dictionary containing:
            - allocation_matrix: Combined allocation matrix (n x m)
            - time_matrix: Actual execution time matrix (n x m)
            - expense_matrix: Actual expense matrix (n x m)
            - user_results: Dict mapping user_id to (time_vector, expense_vector)
        """
        print(f"\n--- Processing Allocations ---")
        
        # Validate we have all users
        if len(allocations) != len(self.user_ids):
            raise ValueError(f"Expected {len(self.user_ids)} allocations, got {len(allocations)}")
        
        # Build allocation matrix (ordered by user_ids)
        allocation_matrix = []
        for user_id in self.user_ids:
            if user_id not in allocations:
                raise ValueError(f"Missing allocation for {user_id}")
            allocation_matrix.append(allocations[user_id])
        
        print("\nAllocation Matrix:")
        for i, user_id in enumerate(self.user_ids):
            print(f"  {user_id}: {allocation_matrix[i]}")
        
        # Calculate actual execution times (with multiplexing)
        time_matrix = calculate_actual_execution_matrix(
            allocation_matrix,
            self.base_execution_times
        )
        
        # Calculate expenses
        expense_matrix = calculate_actual_expense_matrix(
            allocation_matrix,
            self.base_execution_times,
            self.resource_prices
        )
        
        # Print matrices
        print_matrix(time_matrix, "Actual Execution Time Matrix (tij)", precision=2)
        print_matrix(expense_matrix, "Expense Matrix (eij)", precision=2)
        
        # Prepare results for each user
        user_results = {}
        for i, user_id in enumerate(self.user_ids):
            user_results[user_id] = {
                'time_vector': time_matrix[i],
                'expense_vector': expense_matrix[i],
                'max_time': max(time_matrix[i]),
                'total_expense': sum(expense_matrix[i])
            }
            
            print(f"\n{user_id} Results:")
            print(f"  Max time: {user_results[user_id]['max_time']:.2f}s")
            print(f"  Total expense: {user_results[user_id]['total_expense']:.2f}€")
        
        return {
            'allocation_matrix': allocation_matrix,
            'time_matrix': time_matrix,
            'expense_matrix': expense_matrix,
            'user_results': user_results
        }
    
    def check_multiplexing(self, allocation_matrix: List[List[int]]) -> Dict:
        """
        Check which resources are multiplexed
        
        Args:
            allocation_matrix: Allocation matrix (n x m)
        
        Returns:
            Dictionary with multiplexing information
        """
        m_resources = len(allocation_matrix[0])
        multiplexed = {}
        
        for j in range(m_resources):
            count = sum(allocation_matrix[i][j] for i in range(len(allocation_matrix)))
            if count > 1:
                users = [self.user_ids[i] for i in range(len(allocation_matrix)) 
                        if allocation_matrix[i][j] == 1]
                multiplexed[f'R{j+1}'] = {
                    'count': count,
                    'users': users
                }
        
        if multiplexed:
            print(f"\n--- Multiplexed Resources ---")
            for resource, info in multiplexed.items():
                print(f"{resource}: {info['count']} users ({', '.join(info['users'])})")
        else:
            print(f"\n--- No Resource Multiplexing ---")
        
        return multiplexed
    
    def calculate_step2_execution_times(self, 
                                       time_matrix_step1: List[List[float]]) -> List[List[float]]:
        """
        Calculate updated execution times for Step 2
        
        Formula: t_new_ij = t̂_ij + Σ(tij)/n
        
        Args:
            time_matrix_step1: Actual time matrix from Step 1
        
        Returns:
            Updated base execution time matrix for Step 2
        """
        n_tasks = len(time_matrix_step1)
        m_resources = len(time_matrix_step1[0])
        
        updated_times = []
        
        for i in range(n_tasks):
            task_times = []
            for j in range(m_resources):
                # Calculate average of actual times for this resource
                sum_times = sum(time_matrix_step1[k][j] for k in range(n_tasks))
                avg_time = sum_times / n_tasks
                
                # Update formula: new base time = original base time + average
                new_time = self.base_execution_times[i][j] + avg_time
                task_times.append(new_time)
            updated_times.append(task_times)
        
        print(f"\n--- Updated Execution Times for Step 2 ---")
        print_matrix(updated_times, "New Base Execution Times (t̂_new)", precision=2)
        
        return updated_times


def test_resource_manager():
    """Test the Resource Manager with sample allocations"""
    print(f"\n{'='*60}")
    print(f"Testing Resource Manager")
    print(f"{'='*60}")
    
    manager = ResourceManager()
    
    # Test with example allocations from assignment
    test_allocations = {
        'S1': [0, 0, 0, 1, 1],
        'S2': [0, 0, 1, 1, 1],
        'S3': [1, 1, 1, 0, 1]
    }
    
    print(f"\nTest Allocations:")
    for user_id, alloc in test_allocations.items():
        print(f"  {user_id}: {alloc}")
    
    results = manager.process_allocations(test_allocations)
    manager.check_multiplexing(results['allocation_matrix'])
    
    print(f"\n{'='*60}")
    print(f"Resource Manager Test Complete")
    print(f"{'='*60}")
    
    return results


if __name__ == '__main__':
    test_resource_manager()

