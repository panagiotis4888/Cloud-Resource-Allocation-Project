#!/usr/bin/env python3
"""
Convenience script to run various tests
Usage: python3 run_tests.py [test_name]
"""

import sys
import subprocess


TESTS = {
    'config': {
        'desc': 'Test configuration',
        'cmd': 'python3 utils/config.py'
    },
    'calc': {
        'desc': 'Test calculations',
        'cmd': 'python3 utils/calculations.py'
    },
    'optimizer': {
        'desc': 'Test user optimizer',
        'cmd': 'python3 user/optimizer.py'
    },
    'manager': {
        'desc': 'Test resource manager',
        'cmd': 'python3 provider/resource_manager.py'
    },
    'step1': {
        'desc': 'Test Step 1 only',
        'cmd': 'python3 tests/test_step1.py'
    },
    'complete': {
        'desc': 'Test complete flow (Step 1 + Step 2)',
        'cmd': 'python3 tests/test_local_complete.py'
    },
    'all': {
        'desc': 'Run all tests',
        'cmd': None  # Special case
    }
}


def print_menu():
    """Print available tests"""
    print("\n" + "="*60)
    print("Available Tests")
    print("="*60 + "\n")
    
    for name, info in TESTS.items():
        print(f"  {name:<12} - {info['desc']}")
    
    print("\n" + "="*60 + "\n")


def run_test(test_name):
    """Run a specific test"""
    if test_name not in TESTS:
        print(f"Error: Unknown test '{test_name}'")
        print_menu()
        return False
    
    if test_name == 'all':
        # Run all tests except 'all'
        success = True
        for name in TESTS:
            if name != 'all':
                print(f"\n{'='*60}")
                print(f"Running: {name}")
                print(f"{'='*60}\n")
                if not run_test(name):
                    success = False
                print("\n")
        return success
    
    test_info = TESTS[test_name]
    print(f"\nRunning: {test_info['desc']}")
    print(f"Command: {test_info['cmd']}\n")
    
    try:
        result = subprocess.run(test_info['cmd'], shell=True, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"\nError running test: {e}")
        return False
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        return False


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python3 run_tests.py [test_name]")
        print_menu()
        sys.exit(1)
    
    test_name = sys.argv[1]
    success = run_test(test_name)
    
    if success:
        print("\n✓ Test completed successfully")
        sys.exit(0)
    else:
        print("\n✗ Test failed")
        sys.exit(1)


if __name__ == '__main__':
    main()

