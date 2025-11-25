#!/usr/bin/env python
"""
UavNetSim Test Runner

Runs all test files sequentially and reports results.
"""

import sys
import os
import time

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_sanity import run_sanity_check
from test_formation_logic import test_formation_convergence
from test_gui import test_live_visualizer

def run_all_tests(include_gui=False):
    """Run all tests and report results"""
    print("="*70)
    print("UavNetSim Test Suite")
    print("="*70)
    
    results = {}
    total_start = time.time()
    
    total_tests = 3 if include_gui else 2
    test_num = 1
    
    # Test 1: Sanity Check
    print(f"\n[{test_num}/{total_tests}] Running Sanity Check...")
    print("-"*70)
    test_start = time.time()
    try:
        run_sanity_check()
        results['test_sanity'] = ('PASSED', time.time() - test_start)
    except Exception as e:
        results['test_sanity'] = ('FAILED', time.time() - test_start, str(e))
        print(f"ERROR: {e}")
    
    test_num += 1
    
    # Test 2: Formation Logic
    print(f"\n[{test_num}/{total_tests}] Running Formation Logic Test...")
    print("-"*70)
    test_start = time.time()
    try:
        test_formation_convergence()
        results['test_formation'] = ('PASSED', time.time() - test_start)
    except Exception as e:
        results['test_formation'] = ('FAILED', time.time() - test_start, str(e))
        print(f"ERROR: {e}")
    
    test_num += 1
    
    # Test 3: GUI Test (optional)
    if include_gui:
        print(f"\n[{test_num}/{total_tests}] Running GUI Test...")
        print("-"*70)
        test_start = time.time()
        try:
            test_live_visualizer()
            results['test_gui'] = ('PASSED', time.time() - test_start)
        except Exception as e:
            results['test_gui'] = ('FAILED', time.time() - test_start, str(e))
            print(f"ERROR: {e}")
    else:
        print("\n[SKIPPED] GUI test (use --include-gui to run)")
        results['test_gui'] = ('SKIPPED', 0)
    
    total_time = time.time() - total_start
    
    # Summary
    print("\n" + "="*70)
    print("Test Summary")
    print("="*70)
    
    passed = 0
    failed = 0
    skipped = 0
    
    for test_name, result in results.items():
        status = result[0]
        duration = result[1]
        
        if status == 'PASSED':
            passed += 1
            print(f"[PASS] {test_name:30s} {status:8s} ({duration:.2f}s)")
        elif status == 'SKIPPED':
            skipped += 1
            print(f"[SKIP] {test_name:30s} {status:8s}")
        else:
            failed += 1
            error_msg = result[2] if len(result) > 2 else "Unknown error"
            print(f"[FAIL] {test_name:30s} {status:8s} ({duration:.2f}s)")
            print(f"       Error: {error_msg}")
    
    print("-"*70)
    print(f"Tests run: {passed + failed}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    if skipped > 0:
        print(f"Skipped: {skipped}")
    print(f"Total time: {total_time:.2f}s")
    print("="*70)
    
    # Return exit code
    if failed > 0:
        print("\n[RESULT] Some tests failed!")
        return 1
    else:
        print("\n[RESULT] All tests passed!")
        return 0

if __name__ == "__main__":
    # Check for command line arguments
    include_gui = '--include-gui' in sys.argv or '-g' in sys.argv
    
    if '--help' in sys.argv or '-h' in sys.argv:
        print("UavNetSim Test Runner")
        print("\nUsage: uv run tests/run_all_tests.py [options]")
        print("\nOptions:")
        print("  --include-gui, -g    Include GUI test (may pop up windows)")
        print("  --help, -h           Show this help message")
        sys.exit(0)
    
    exit_code = run_all_tests(include_gui=include_gui)
    sys.exit(exit_code)

