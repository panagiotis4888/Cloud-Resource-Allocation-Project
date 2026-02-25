"""
Test script for Step 1: Independent Optimization
Tests the complete flow from user optimization to provider calculation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from user.optimizer import UserOptimizer
from provider.resource_manager import ResourceManager
from utils.config import USER_IDS


def test_step1_complete():
    """
    Test complete Step 1 flow:
    1. Each user optimizes independently
    2. Provider calculates actual times/expenses with multiplexing
    3. Users calculate actual utilities
    """
    
    print("\n" + "="*80)
    print("STEP 1: INDEPENDENT OPTIMIZATION TEST")
    print("="*80)
    
    # Step 1.1: Each user optimizes independently
    print("\n### PHASE 1: User Optimization ###")
    user_optimizers = {}
    allocations = {}
    
    for user_id in USER_IDS:
        optimizer = UserOptimizer(user_id)
        allocation, expected_utility = optimizer.optimize_step1()
        user_optimizers[user_id] = optimizer
        allocations[user_id] = allocation
    
    # Step 1.2: Provider processes allocations
    print("\n\n### PHASE 2: Provider Processing ###")
    manager = ResourceManager()
    results = manager.process_allocations(allocations)
    manager.check_multiplexing(results['allocation_matrix'])
    
    # Step 1.3: Users calculate actual utilities
    print("\n\n### PHASE 3: Actual Utility Calculation ###")
    summary = []
    
    for user_id in USER_IDS:
        optimizer = user_optimizers[user_id]
        user_result = results['user_results'][user_id]
        
        actual_utility = optimizer.calculate_actual_utility_from_matrices(
            user_result['time_vector'],
            user_result['expense_vector']
        )
        
        summary.append({
            'user_id': user_id,
            'allocation': optimizer.optimal_allocation,
            'expected_utility': optimizer.optimal_utility,
            'actual_utility': actual_utility,
            'utility_loss': optimizer.optimal_utility - actual_utility,
            'max_time': user_result['max_time'],
            'total_expense': user_result['total_expense']
        })
    
    # Print summary table
    print("\n\n" + "="*80)
    print("STEP 1 RESULTS SUMMARY")
    print("="*80)
    print(f"\n{'User':<6} {'Allocation Vector':<25} {'Expected U':<12} {'Actual U':<12} {'Loss':<10}")
    print("-" * 80)
    
    for s in summary:
        alloc_str = f"({', '.join(map(str, s['allocation']))})"
        print(f"{s['user_id']:<6} {alloc_str:<25} {s['expected_utility']:<12.4f} "
              f"{s['actual_utility']:<12.4f} {s['utility_loss']:<10.4f}")
    
    print("\n" + "-" * 80)
    print(f"Total Expected Utility: {sum(s['expected_utility'] for s in summary):.4f}")
    print(f"Total Actual Utility:   {sum(s['actual_utility'] for s in summary):.4f}")
    print(f"Total Utility Loss:     {sum(s['utility_loss'] for s in summary):.4f}")
    
    # Check constraints
    print("\n\n### CONSTRAINT VERIFICATION ###")
    for s in summary:
        user_id = s['user_id']
        optimizer = user_optimizers[user_id]
        deadline = optimizer.deadline
        budget = optimizer.budget
        
        time_ok = "✓" if s['max_time'] <= deadline else "✗"
        budget_ok = "✓" if s['total_expense'] <= budget else "✗"
        
        print(f"{user_id}: Time {time_ok} ({s['max_time']:.2f}s ≤ {deadline}s), "
              f"Budget {budget_ok} ({s['total_expense']:.2f}€ ≤ {budget}€)")
    
    print("\n" + "="*80)
    print("STEP 1 TEST COMPLETE")
    print("="*80 + "\n")
    
    return summary, results


if __name__ == '__main__':
    test_step1_complete()

