"""Test script for the LangGraph orchestration pipeline.

This script tests the complete workflow execution with mock data.
"""

import logging
import sys
from pathlib import Path

# Add the ai-engine directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from graph.workflow import execute_workflow, get_workflow_visualization

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def test_workflow_visualization():
    """Test workflow visualization."""
    print("\n" + "=" * 70)
    print("TEST 1: WORKFLOW VISUALIZATION")
    print("=" * 70)
    
    try:
        visualization = get_workflow_visualization()
        print(visualization)
        print("✓ Workflow visualization generated successfully")
        return True
    except Exception as e:
        print(f"✗ Workflow visualization failed: {e}")
        return False


def test_workflow_execution():
    """Test complete workflow execution."""
    print("\n" + "=" * 70)
    print("TEST 2: WORKFLOW EXECUTION")
    print("=" * 70)
    
    try:
        # Execute workflow with test data
        result = execute_workflow(
            repo_id="test-repo-001",
            repo_path="/test/path/to/repository"
        )
        
        # Verify result structure
        print("\n--- Result Summary ---")
        print(f"Repo ID: {result['repo_id']}")
        print(f"Status: {result['status']}")
        print(f"Timestamp: {result['timestamp']}")
        print(f"Error: {result.get('error', 'None')}")
        
        # Check logs
        print(f"\n--- Execution Logs ({len(result['logs'])} entries) ---")
        for log in result['logs']:
            print(f"  [{log['status']}] {log['node']}: {log['message']}")
        
        # Check parsed_repo
        if result.get('parsed_repo'):
            print(f"\n--- Repository Analysis ---")
            metadata = result['parsed_repo'].get('metadata', {})
            print(f"  Total files: {metadata.get('total_files', 0)}")
            print(f"  Total lines: {metadata.get('total_lines', 0)}")
            print(f"  Languages: {', '.join(metadata.get('languages', []))}")
        
        # Check dependency_graph
        if result.get('dependency_graph'):
            print(f"\n--- Dependency Analysis ---")
            metrics = result['dependency_graph'].get('metrics', {})
            print(f"  Total dependencies: {metrics.get('total_dependencies', 0)}")
            print(f"  Circular dependencies: {metrics.get('circular_dependencies', 0)}")
            print(f"  Max depth: {metrics.get('max_depth', 0)}")
        
        # Check fragility_scores
        if result.get('fragility_scores'):
            print(f"\n--- Fragility Analysis ---")
            summary = result['fragility_scores'].get('summary', {})
            print(f"  Average fragility: {summary.get('average_fragility', 0):.2f}")
            print(f"  High risk components: {summary.get('high_risk_count', 0)}")
            print(f"  Medium risk components: {summary.get('medium_risk_count', 0)}")
            print(f"  Low risk components: {summary.get('low_risk_count', 0)}")
        
        # Check incidents
        if result.get('incidents'):
            print(f"\n--- Incident Detection ({len(result['incidents'])} incidents) ---")
            for incident in result['incidents']:
                print(f"  [{incident['severity'].upper()}] {incident['id']}: {incident['title']}")
                print(f"    Component: {incident['component']}")
                print(f"    Recommendations: {len(incident.get('recommendations', []))}")
        
        # Check mentor_context
        if result.get('mentor_context'):
            print(f"\n--- Mentor Guidance ---")
            summary = result['mentor_context'].get('summary', {})
            print(f"  Total incidents: {summary.get('total_incidents', 0)}")
            print(f"  Priority actions: {summary.get('priority_actions', 0)}")
            print(f"  Estimated effort: {summary.get('estimated_effort', 'N/A')}")
            
            recommendations = result['mentor_context'].get('recommendations', [])
            print(f"\n  Recommendations ({len(recommendations)}):")
            for rec in recommendations:
                print(f"    [{rec['priority'].upper()}] {rec['title']}")
                print(f"      Category: {rec['category']}")
                print(f"      Effort: {rec.get('estimated_effort', 'N/A')}")
        
        # Verify all expected fields are present
        expected_fields = [
            'repo_id', 'repo_path', 'status', 'logs', 'timestamp',
            'parsed_repo', 'dependency_graph', 'fragility_scores',
            'incidents', 'mentor_context'
        ]
        
        missing_fields = [field for field in expected_fields if field not in result]
        if missing_fields:
            print(f"\n✗ Missing fields: {', '.join(missing_fields)}")
            return False
        
        # Verify status
        if result['status'] != 'completed':
            print(f"\n✗ Unexpected status: {result['status']}")
            return False
        
        print("\n✓ Workflow execution completed successfully")
        return True
        
    except Exception as e:
        print(f"\n✗ Workflow execution failed: {e}")
        logger.exception("Workflow execution error")
        return False


def test_error_handling():
    """Test error handling with invalid input."""
    print("\n" + "=" * 70)
    print("TEST 3: ERROR HANDLING")
    print("=" * 70)
    
    try:
        # This should handle gracefully even with invalid path
        result = execute_workflow(
            repo_id="error-test",
            repo_path="/invalid/path"
        )
        
        print(f"Status: {result['status']}")
        print(f"Error: {result.get('error', 'None')}")
        
        # Check that logs were still created
        if result['logs']:
            print(f"Logs created: {len(result['logs'])} entries")
        
        print("✓ Error handling works correctly")
        return True
        
    except Exception as e:
        print(f"✗ Error handling test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("INCIDENTOS ORCHESTRATION PIPELINE - TEST SUITE")
    print("=" * 70)
    
    results = []
    
    # Run tests
    results.append(("Workflow Visualization", test_workflow_visualization()))
    results.append(("Workflow Execution", test_workflow_execution()))
    results.append(("Error Handling", test_error_handling()))
    
    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{status}: {test_name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())

# Made with Bob
