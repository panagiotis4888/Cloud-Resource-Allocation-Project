"""
User optimization logic for resource allocation
Implements brute-force optimization with constraint checking
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.calculations import (
    generate_valid_allocations,
    calculate_utility,
    check_constraints,
    calculate_actual_utility,
    format_allocation_vector
)
from utils.config import (
    NUM_SUBTASKS,
    NUM_RESOURCES,
    RESOURCE_PRICES,
    TASK_CONSTRAINTS,
    WEIGHTS_TIME,
    WEIGHTS_EXPENSE,
    get_execution_times
)
from typing import List, Tuple, Dict


class UserOptimizer:
    """
    Optimizer for a single user (task)
    Performs brute-force optimization to find best allocation strategy
    """
    
    def __init__(self, user_id: str):
        """
        Initialize optimizer for a specific user
        
        Args:
            user_id: User identifier (S1, S2, or S3)
        """
        self.user_id = user_id
        self.num_subtasks = NUM_SUBTASKS[user_id]
        self.num_resources = NUM_RESOURCES
        self.execution_times = get_execution_times(user_id)
        self.resource_prices = RESOURCE_PRICES
        self.weight_time = WEIGHTS_TIME[user_id]
        self.weight_expense = WEIGHTS_EXPENSE[user_id]
        self.deadline = TASK_CONSTRAINTS[user_id]['deadline']
        self.budget = TASK_CONSTRAINTS[user_id]['budget']
        
        self.optimal_allocation = None
        self.optimal_utility = 0
        
        print(f"\n=== Initialized Optimizer for {user_id} ===")
        print(f"Subtasks: {self.num_subtasks}")
        print(f"Weights: wt={self.weight_time:.2f}, we={self.weight_expense:.2f}")
        print(f"Constraints: T≤{self.deadline}s, M≤{self.budget}€")
    
    def optimize_step1(self, custom_execution_times: List[float] = None) -> Tuple[List[int], float]:
        """
        Perform Step 1 optimization (independent, no multiplexing)
        
        Args:
            custom_execution_times: Optional custom execution times (for Step 2)
        
        Returns:
            Tuple of (optimal_allocation_vector, expected_utility)
        """
        exec_times = custom_execution_times if custom_execution_times else self.execution_times
        
        print(f"\n--- Optimizing {self.user_id} (Step 1) ---")
        print(f"Execution times: {exec_times}")
        
        # Generate all valid allocations
        all_allocations = generate_valid_allocations(self.num_subtasks, self.num_resources)
        print(f"Evaluating {len(all_allocations)} possible allocations...")
        
        best_allocation = None
        best_utility = 0
        feasible_count = 0
        
        for allocation in all_allocations:
            # Check constraints
            if not check_constraints(allocation, exec_times, self.resource_prices,
                                    self.deadline, self.budget):
                continue
            
            feasible_count += 1
            
            # Calculate utility
            utility = calculate_utility(allocation, exec_times, self.resource_prices,
                                       self.weight_time, self.weight_expense)
            
            # Update best if this is better
            if utility > best_utility:
                best_utility = utility
                best_allocation = allocation
        
        if best_allocation is None:
            print(f"WARNING: No feasible allocation found for {self.user_id}!")
            # Return a default allocation (first valid one)
            best_allocation = all_allocations[0]
            best_utility = calculate_utility(best_allocation, exec_times, self.resource_prices,
                                            self.weight_time, self.weight_expense)
        
        self.optimal_allocation = best_allocation
        self.optimal_utility = best_utility
        
        print(f"Feasible allocations: {feasible_count}/{len(all_allocations)}")
        print(f"Optimal allocation: {format_allocation_vector(best_allocation)}")
        print(f"Expected utility: {best_utility:.4f}")
        
        return best_allocation, best_utility
    
    def calculate_actual_utility_from_matrices(self, 
                                              time_vector: List[float],
                                              expense_vector: List[float]) -> float:
        """
        Calculate actual utility given time and expense vectors from provider
        
        Args:
            time_vector: Actual execution times for each resource
            expense_vector: Actual expenses for each resource
        
        Returns:
            Actual utility value
        """
        actual_utility = calculate_actual_utility(
            self.optimal_allocation,
            time_vector,
            expense_vector,
            self.weight_time,
            self.weight_expense
        )
        
        print(f"\n--- Actual Utility for {self.user_id} ---")
        print(f"Time vector: {[f'{t:.2f}' for t in time_vector]}")
        print(f"Expense vector: {[f'{e:.2f}' for e in expense_vector]}")
        print(f"Actual utility: {actual_utility:.4f}")
        print(f"Utility loss: {self.optimal_utility - actual_utility:.4f}")
        
        return actual_utility
    
    def get_results_dict(self) -> Dict:
        """Get optimization results as dictionary"""
        return {
            'user_id': self.user_id,
            'allocation_vector': self.optimal_allocation,
            'expected_utility': self.optimal_utility,
            'num_subtasks': self.num_subtasks,
            'weights': {
                'time': self.weight_time,
                'expense': self.weight_expense
            },
            'constraints': {
                'deadline': self.deadline,
                'budget': self.budget
            }
        }


def test_optimizer(user_id: str = 'S1'):
    """Test the optimizer for a single user"""
    print(f"\n{'='*60}")
    print(f"Testing Optimizer for {user_id}")
    print(f"{'='*60}")
    
    optimizer = UserOptimizer(user_id)
    allocation, utility = optimizer.optimize_step1()
    
    print(f"\n{'='*60}")
    print(f"Optimization Complete")
    print(f"{'='*60}")
    
    return optimizer


if __name__ == '__main__':
    # Test all three users
    for user_id in ['S1', 'S2', 'S3']:
        test_optimizer(user_id)
        print("\n")

