#!/usr/bin/env python3
"""
Test Runner for IncidentOS Agent Pipeline
Standalone script to execute all tests with detailed reporting.
"""
import sys
import os
from pathlib import Path

# Add ai-engine directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import test modules
from tests.test_repository_agent import run_tests as run_repository_tests
from tests.test_integrated_workflow import run_integrated_tests


def main():
    """Main test runner entry point."""
    print("=" * 80)
    print("INCIDENTOS - COMPREHENSIVE AGENT PIPELINE TEST SUITE")
    print("=" * 80)
    print()
    print("This test suite validates:")
    print("  - Repository Agent (Workflow 4)")
    print("  - Git History Agent (Workflow 6)")
    print("  - Integrated Pipeline (Both agents in tandem)")
    print("  - Contract compliance for all workflows")
    print("  - Edge case handling and error recovery")
    print("  - GitPython mocking and realistic commit simulation")
    print()
    print("=" * 80)
    print()
    
    all_successful = True
    total_tests = 0
    total_failures = 0
    total_errors = 0
    
    # Run Repository Agent tests
    print("\n" + "=" * 80)
    print("PHASE 1: REPOSITORY AGENT TESTS")
    print("=" * 80)
    print()
    
    repo_result = run_repository_tests()
    total_tests += repo_result.testsRun
    total_failures += len(repo_result.failures)
    total_errors += len(repo_result.errors)
    
    if not repo_result.wasSuccessful():
        all_successful = False
    
    # Run Integrated Workflow tests
    print("\n" + "=" * 80)
    print("PHASE 2: INTEGRATED WORKFLOW TESTS")
    print("=" * 80)
    print()
    
    integrated_result = run_integrated_tests()
    total_tests += integrated_result.testsRun
    total_failures += len(integrated_result.failures)
    total_errors += len(integrated_result.errors)
    
    if not integrated_result.wasSuccessful():
        all_successful = False
    
    # Print final summary
    print()
    print("=" * 80)
    print("FINAL RESULTS - ALL TEST PHASES")
    print("=" * 80)
    print(f"Total tests run: {total_tests}")
    print(f"Successes: {total_tests - total_failures - total_errors}")
    print(f"Failures: {total_failures}")
    print(f"Errors: {total_errors}")
    print()
    
    if all_successful:
        print("[SUCCESS] ALL TESTS PASSED")
        print()
        print("The IncidentOS agent pipeline is ready for production!")
        print("- Repository Agent: Workflow 4 contract validated")
        print("- Git History Agent: Workflow 6 contract validated")
        print("- Integrated Pipeline: End-to-end workflow validated")
        print("- All edge cases handled with proper fallbacks")
        return 0
    else:
        print("[FAIL] SOME TESTS FAILED")
        print()
        print("Please review the failures above and fix the issues.")
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)

# Made with Bob
