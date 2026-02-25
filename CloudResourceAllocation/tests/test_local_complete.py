"""
Complete local test without AWS dependencies
Tests both Step 1 and Step 2 of the resource allocation game
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from user.optimizer import UserOptimizer
from provider.resource_manager import ResourceManager
from utils.config import USER_IDS
from utils.calculations import format_allocation_vector


def print_separator(title):
    """Print a formatted separator"""
    print("\n" + "="*80)
    print(f" {title}")
    print("="*80 + "\n")


def test_complete_flow():
    """Test complete flow including Step 1 and Step 2"""
    
    print_separator("CLOUD RESOURCE ALLOCATION - COMPLETE TEST")
    
    # ===== STEP 1 =====
    print_separator("STEP 1: INDEPENDENT OPTIMIZATION")
    
    # Phase 1.1: User Optimization
    print("\n### PHASE 1.1: User Optimization (Independent) ###\n")
    
    user_optimizers = {}
    allocations_step1 = {}
    
    for user_id in USER_IDS:
        print(f"\n--- Optimizing {user_id} ---")
        optimizer = UserOptimizer(user_id)
        allocation, expected_utility = optimizer.optimize_step1()
        user_optimizers[user_id] = optimizer
        allocations_step1[user_id] = allocation
        print(f"{user_id}: {format_allocation_vector(allocation)} → utility = {expected_utility:.4f}")
    
    # Phase 1.2: Provider Processing
    print("\n\n### PHASE 1.2: Provider Processing (With Multiplexing) ###\n")
    
    manager = ResourceManager()
    results_step1 = manager.process_allocations(allocations_step1)
    multiplexing_step1 = manager.check_multiplexing(results_step1['allocation_matrix'])
    
    # Phase 1.3: Calculate Actual Utilities
    print("\n\n### PHASE 1.3: Actual Utility Calculation ###\n")
    
    summary_step1 = []
    
    for user_id in USER_IDS:
        optimizer = user_optimizers[user_id]
        user_result = results_step1['user_results'][user_id]
        
        actual_utility = optimizer.calculate_actual_utility_from_matrices(
            user_result['time_vector'],
            user_result['expense_vector']
        )
        
        summary_step1.append({
            'user_id': user_id,
            'allocation': optimizer.optimal_allocation,
            'expected_utility': optimizer.optimal_utility,
            'actual_utility': actual_utility,
            'utility_loss': optimizer.optimal_utility - actual_utility,
            'max_time': user_result['max_time'],
            'total_expense': user_result['total_expense']
        })
    
    # Print Step 1 Summary
    print_separator("STEP 1 RESULTS")
    print(f"\n{'User':<6} {'Allocation Vector':<25} {'Expected U':<12} {'Actual U':<12} {'Loss':<10}")
    print("-" * 75)
    
    for s in summary_step1:
        alloc_str = format_allocation_vector(s['allocation'])
        print(f"{s['user_id']:<6} {alloc_str:<25} {s['expected_utility']:<12.4f} "
              f"{s['actual_utility']:<12.4f} {s['utility_loss']:<10.4f}")
    
    print("\n" + "-" * 75)
    print(f"Total Expected Utility: {sum(s['expected_utility'] for s in summary_step1):.4f}")
    print(f"Total Actual Utility:   {sum(s['actual_utility'] for s in summary_step1):.4f}")
    print(f"Total Utility Loss:     {sum(s['utility_loss'] for s in summary_step1):.4f}")
    
    # ===== STEP 2 =====
    print_separator("STEP 2: STRATEGY UPDATE WITH UPDATED EXECUTION TIMES")
    
    # Calculate updated execution times
    print("\n### PHASE 2.1: Calculate Updated Execution Times ###\n")
    
    updated_times = manager.calculate_step2_execution_times(results_step1['time_matrix'])
    
    # Phase 2.2: Re-optimize with updated times
    print("\n\n### PHASE 2.2: User Re-optimization ###\n")
    
    allocations_step2 = {}
    
    for i, user_id in enumerate(USER_IDS):
        print(f"\n--- Re-optimizing {user_id} with updated times ---")
        optimizer = user_optimizers[user_id]
        allocation, expected_utility = optimizer.optimize_step1(custom_execution_times=updated_times[i])
        allocations_step2[user_id] = allocation
        print(f"{user_id}: {format_allocation_vector(allocation)} → utility = {expected_utility:.4f}")
    
    # Phase 2.3: Provider processes Step 2
    print("\n\n### PHASE 2.3: Provider Processing (Step 2) ###\n")
    
    # For Step 2, we use the ORIGINAL base execution times for actual calculation
    # The updated times were only for user optimization
    results_step2 = manager.process_allocations(allocations_step2)
    multiplexing_step2 = manager.check_multiplexing(results_step2['allocation_matrix'])
    
    # Phase 2.4: Calculate Step 2 Actual Utilities
    print("\n\n### PHASE 2.4: Step 2 Actual Utilities ###\n")
    
    summary_step2 = []
    
    for user_id in USER_IDS:
        optimizer = user_optimizers[user_id]
        user_result = results_step2['user_results'][user_id]
        
        actual_utility = optimizer.calculate_actual_utility_from_matrices(
            user_result['time_vector'],
            user_result['expense_vector']
        )
        
        summary_step2.append({
            'user_id': user_id,
            'allocation': optimizer.optimal_allocation,
            'expected_utility': optimizer.optimal_utility,
            'actual_utility': actual_utility,
            'utility_loss': optimizer.optimal_utility - actual_utility,
            'max_time': user_result['max_time'],
            'total_expense': user_result['total_expense']
        })
    
    # Print Step 2 Summary
    print_separator("STEP 2 RESULTS")
    print(f"\n{'User':<6} {'Allocation Vector':<25} {'Expected U':<12} {'Actual U':<12} {'Loss':<10}")
    print("-" * 75)
    
    for s in summary_step2:
        alloc_str = format_allocation_vector(s['allocation'])
        print(f"{s['user_id']:<6} {alloc_str:<25} {s['expected_utility']:<12.4f} "
              f"{s['actual_utility']:<12.4f} {s['utility_loss']:<10.4f}")
    
    print("\n" + "-" * 75)
    print(f"Total Expected Utility: {sum(s['expected_utility'] for s in summary_step2):.4f}")
    print(f"Total Actual Utility:   {sum(s['actual_utility'] for s in summary_step2):.4f}")
    print(f"Total Utility Loss:     {sum(s['utility_loss'] for s in summary_step2):.4f}")
    
    # ===== COMPARISON =====
    print_separator("COMPARISON: STEP 1 vs STEP 2")
    
    print(f"\n{'User':<6} {'Step 1 Actual U':<18} {'Step 2 Actual U':<18} {'Improvement':<12}")
    print("-" * 60)
    
    for i, user_id in enumerate(USER_IDS):
        s1_utility = summary_step1[i]['actual_utility']
        s2_utility = summary_step2[i]['actual_utility']
        improvement = s2_utility - s1_utility
        symbol = "+" if improvement > 0 else ""
        print(f"{user_id:<6} {s1_utility:<18.4f} {s2_utility:<18.4f} {symbol}{improvement:<12.4f}")
    
    print("\n" + "-" * 60)
    total_s1 = sum(s['actual_utility'] for s in summary_step1)
    total_s2 = sum(s['actual_utility'] for s in summary_step2)
    total_improvement = total_s2 - total_s1
    symbol = "+" if total_improvement > 0 else ""
    print(f"{'Total':<6} {total_s1:<18.4f} {total_s2:<18.4f} {symbol}{total_improvement:<12.4f}")
    
    # ===== CONSTRAINT VERIFICATION =====
    print_separator("CONSTRAINT VERIFICATION")
    
    print("\nStep 1 Constraints:")
    for s in summary_step1:
        user_id = s['user_id']
        optimizer = user_optimizers[user_id]
        time_ok = "✓" if s['max_time'] <= optimizer.deadline else "✗"
        budget_ok = "✓" if s['total_expense'] <= optimizer.budget else "✗"
        print(f"  {user_id}: Time {time_ok} ({s['max_time']:.2f} ≤ {optimizer.deadline}), "
              f"Budget {budget_ok} ({s['total_expense']:.2f} ≤ {optimizer.budget})")
    
    print("\nStep 2 Constraints:")
    for s in summary_step2:
        user_id = s['user_id']
        optimizer = user_optimizers[user_id]
        time_ok = "✓" if s['max_time'] <= optimizer.deadline else "✗"
        budget_ok = "✓" if s['total_expense'] <= optimizer.budget else "✗"
        print(f"  {user_id}: Time {time_ok} ({s['max_time']:.2f} ≤ {optimizer.deadline}), "
              f"Budget {budget_ok} ({s['total_expense']:.2f} ≤ {optimizer.budget})")
    
    print_separator("TEST COMPLETE")
    
    return summary_step1, summary_step2


if __name__ == '__main__':
    test_complete_flow()

