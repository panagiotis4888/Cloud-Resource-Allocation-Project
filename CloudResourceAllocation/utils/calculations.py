"""
Core calculation utilities for resource allocation game
Includes allocation generation, utility calculations, and matrix operations
"""

import numpy as np
from itertools import combinations
from typing import List, Tuple, Dict


def generate_valid_allocations(num_subtasks: int, num_resources: int) -> List[List[int]]:
    """
    Generate all valid allocation vectors for a task.
    
    Constraints:
    - Each subtask must be assigned to exactly one resource (sum of row = 1)
    - Each resource can have at most one subtask (sum of column ≤ 1)
    
    Args:
        num_subtasks: Number of subtasks (k)
        num_resources: Number of available resources (m)
    
    Returns:
        List of allocation vectors (each is a list of length m)
    """
    if num_subtasks > num_resources:
        raise ValueError("Cannot allocate more subtasks than resources")
    
    valid_allocations = []
    
    # Choose which num_subtasks resources to use from num_resources available
    for resource_combination in combinations(range(num_resources), num_subtasks):
        # For each combination, create allocation vector
        allocation = [0] * num_resources
        for resource_idx in resource_combination:
            allocation[resource_idx] = 1
        valid_allocations.append(allocation)
    
    return valid_allocations


def calculate_execution_time_vector(allocation_vector: List[int], 
                                    execution_times: List[float]) -> List[float]:
    """
    Calculate execution time for each resource given allocation.
    
    Args:
        allocation_vector: Allocation vector (1 if subtask assigned, 0 otherwise)
        execution_times: Base execution time for each resource
    
    Returns:
        Time vector (tij for each resource j)
    """
    time_vector = []
    for j in range(len(allocation_vector)):
        if allocation_vector[j] == 1:
            time_vector.append(execution_times[j])
        else:
            time_vector.append(0)
    return time_vector


def calculate_expense_vector(allocation_vector: List[int],
                             execution_times: List[float],
                             resource_prices: List[float]) -> List[float]:
    """
    Calculate expense for each resource given allocation.
    
    Formula: eij = aij * t̂ij * pj
    
    Args:
        allocation_vector: Allocation vector
        execution_times: Base execution time for each resource
        resource_prices: Price for each resource
    
    Returns:
        Expense vector (eij for each resource j)
    """
    expense_vector = []
    for j in range(len(allocation_vector)):
        expense = allocation_vector[j] * execution_times[j] * resource_prices[j]
        expense_vector.append(expense)
    return expense_vector


def calculate_utility(allocation_vector: List[int],
                     execution_times: List[float],
                     resource_prices: List[float],
                     weight_time: float,
                     weight_expense: float) -> float:
    """
    Calculate utility for a given allocation.
    
    Formula: ui(ai) = 1 / (wt * max(tij) + we * sum(eij))
    
    Args:
        allocation_vector: Allocation vector
        execution_times: Base execution time for each resource
        resource_prices: Price for each resource
        weight_time: Weight for execution time (wt)
        weight_expense: Weight for expense (we)
    
    Returns:
        Utility value
    """
    time_vector = calculate_execution_time_vector(allocation_vector, execution_times)
    expense_vector = calculate_expense_vector(allocation_vector, execution_times, resource_prices)
    
    max_time = max(time_vector)
    total_expense = sum(expense_vector)
    
    denominator = weight_time * max_time + weight_expense * total_expense
    
    if denominator == 0:
        return 0
    
    return 1.0 / denominator


def check_constraints(allocation_vector: List[int],
                     execution_times: List[float],
                     resource_prices: List[float],
                     deadline: float,
                     budget: float) -> bool:
    """
    Check if allocation satisfies deadline and budget constraints.
    
    Args:
        allocation_vector: Allocation vector
        execution_times: Base execution time for each resource
        resource_prices: Price for each resource
        deadline: Maximum allowed time
        budget: Maximum allowed budget
    
    Returns:
        True if constraints are satisfied, False otherwise
    """
    time_vector = calculate_execution_time_vector(allocation_vector, execution_times)
    expense_vector = calculate_expense_vector(allocation_vector, execution_times, resource_prices)
    
    max_time = max(time_vector)
    total_expense = sum(expense_vector)
    
    return max_time <= deadline and total_expense <= budget


def calculate_actual_execution_matrix(allocation_matrix: List[List[int]],
                                     base_execution_times: List[List[float]]) -> List[List[float]]:
    """
    Calculate actual execution time matrix accounting for multiplexing.
    
    When multiple users share a resource, execution time increases proportionally.
    Formula: tij = (Σ_i aij) * t̂ij
    
    Args:
        allocation_matrix: Matrix of allocation vectors (n x m)
        base_execution_times: Base execution time matrix (n x m)
    
    Returns:
        Actual execution time matrix (n x m)
    """
    n_tasks = len(allocation_matrix)
    m_resources = len(allocation_matrix[0])
    
    actual_times = []
    
    for i in range(n_tasks):
        task_times = []
        for j in range(m_resources):
            # Count how many tasks assigned subtasks to resource j
            multiplexing_factor = sum(allocation_matrix[k][j] for k in range(n_tasks))
            
            # Calculate actual time for this task on this resource
            if allocation_matrix[i][j] == 1:
                actual_time = multiplexing_factor * base_execution_times[i][j]
            else:
                actual_time = 0
            
            task_times.append(actual_time)
        actual_times.append(task_times)
    
    return actual_times


def calculate_actual_expense_matrix(allocation_matrix: List[List[int]],
                                   base_execution_times: List[List[float]],
                                   resource_prices: List[float]) -> List[List[float]]:
    """
    Calculate actual expense matrix.
    
    Formula: eij = aij * t̂ij * pj
    
    Args:
        allocation_matrix: Matrix of allocation vectors (n x m)
        base_execution_times: Base execution time matrix (n x m)
        resource_prices: Price vector for resources
    
    Returns:
        Expense matrix (n x m)
    """
    n_tasks = len(allocation_matrix)
    m_resources = len(allocation_matrix[0])
    
    expense_matrix = []
    
    for i in range(n_tasks):
        task_expenses = []
        for j in range(m_resources):
            expense = allocation_matrix[i][j] * base_execution_times[i][j] * resource_prices[j]
            task_expenses.append(expense)
        expense_matrix.append(task_expenses)
    
    return expense_matrix


def calculate_actual_utility(allocation_vector: List[int],
                            actual_time_vector: List[float],
                            actual_expense_vector: List[float],
                            weight_time: float,
                            weight_expense: float) -> float:
    """
    Calculate actual utility given actual (multiplexed) times and expenses.
    
    Args:
        allocation_vector: Allocation vector
        actual_time_vector: Actual execution times (with multiplexing)
        actual_expense_vector: Actual expenses
        weight_time: Weight for time
        weight_expense: Weight for expense
    
    Returns:
        Actual utility value
    """
    max_time = max(actual_time_vector) if max(actual_time_vector) > 0 else 0
    total_expense = sum(actual_expense_vector)
    
    denominator = weight_time * max_time + weight_expense * total_expense
    
    if denominator == 0:
        return 0
    
    return 1.0 / denominator


def update_execution_times_step2(actual_times_step1: List[List[float]],
                                 base_execution_times: List[List[float]]) -> List[List[float]]:
    """
    Update execution times for Step 2 using the formula:
    t_new_ij = t̂_ij + Σ(tij)/n
    
    Args:
        actual_times_step1: Actual execution times from Step 1
        base_execution_times: Base execution time matrix
    
    Returns:
        Updated execution time matrix for Step 2
    """
    n_tasks = len(actual_times_step1)
    m_resources = len(actual_times_step1[0])
    
    updated_times = []
    
    for i in range(n_tasks):
        task_times = []
        for j in range(m_resources):
            # Calculate average of actual times for this resource across all tasks
            sum_times = sum(actual_times_step1[k][j] for k in range(n_tasks))
            avg_time = sum_times / n_tasks
            
            # Update formula
            new_time = base_execution_times[i][j] + avg_time
            task_times.append(new_time)
        updated_times.append(task_times)
    
    return updated_times


def format_allocation_vector(allocation_vector: List[int]) -> str:
    """Format allocation vector as string for display"""
    return f"({', '.join(map(str, allocation_vector))})"


def print_matrix(matrix: List[List[float]], name: str, precision: int = 2):
    """Pretty print a matrix"""
    print(f"\n{name}:")
    for i, row in enumerate(matrix):
        formatted_row = [f"{val:.{precision}f}" for val in row]
        print(f"  Task {i+1}: [{', '.join(formatted_row)}]")


if __name__ == '__main__':
    # Test the functions
    print("Testing allocation generation:")
    allocations = generate_valid_allocations(num_subtasks=2, num_resources=5)
    print(f"Generated {len(allocations)} valid allocations for 2 subtasks on 5 resources")
    print("First 5 allocations:")
    for alloc in allocations[:5]:
        print(f"  {format_allocation_vector(alloc)}")

