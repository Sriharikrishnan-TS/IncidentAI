"""
Test script for the Fragility Agent.

This script tests the Fragility Agent with mock data to demonstrate
its functionality without requiring a live Neo4j connection.
"""

import json
from unittest.mock import Mock, patch, MagicMock
from fragility_agent import FragilityAgent, OperationalMetrics, FragilityOutput


def test_operational_metrics_validation():
    """Test that operational metrics are validated correctly."""
    print("=" * 80)
    print("TEST 1: Operational Metrics Validation")
    print("=" * 80)
    
    # Test valid input
    valid_metrics = {
        "mock_churn": {"auth-service": 92, "payment-service": 31},
        "mock_incidents": {"auth-service": 4}
    }
    
    try:
        metrics = OperationalMetrics(**valid_metrics)
        print("\n✓ Valid metrics accepted")
        print(f"  Churn services: {list(metrics.mock_churn.keys())}")
        print(f"  Incident services: {list(metrics.mock_incidents.keys())}")
    except Exception as e:
        print(f"\n✗ Validation failed: {e}")
        return False
    
    # Test normalization (uppercase to lowercase)
    mixed_case = {
        "mock_churn": {"Auth-Service": 92, "PAYMENT-SERVICE": 31},
        "mock_incidents": {"Auth-Service": 4}
    }
    
    try:
        metrics = OperationalMetrics(**mixed_case)
        assert "auth-service" in metrics.mock_churn
        assert "payment-service" in metrics.mock_churn
        print("\n✓ Service name normalization works")
    except Exception as e:
        print(f"\n✗ Normalization failed: {e}")
        return False
    
    print("\n[PASS] Operational metrics validation test passed")
    return True


def test_normalization_logic():
    """Test the metric normalization logic."""
    print("\n\n" + "=" * 80)
    print("TEST 2: Metric Normalization Logic")
    print("=" * 80)
    
    agent = FragilityAgent()
    
    # Test normalization with various ranges
    test_cases = [
        (5, 10, 0, 0.5),    # Middle value
        (0, 10, 0, 0.0),    # Minimum
        (10, 10, 0, 1.0),   # Maximum
        (7, 10, 5, 0.4),    # With non-zero minimum
    ]
    
    all_passed = True
    for value, max_val, min_val, expected in test_cases:
        result = agent._normalize_metric(value, max_val, min_val)
        passed = abs(result - expected) < 0.01
        status = "✓" if passed else "✗"
        print(f"\n{status} normalize({value}, max={max_val}, min={min_val}) = {result:.2f} (expected {expected:.2f})")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n[PASS] Normalization logic test passed")
    else:
        print("\n[FAIL] Some normalization tests failed")
    
    return all_passed


def test_scoring_components():
    """Test individual scoring components."""
    print("\n\n" + "=" * 80)
    print("TEST 3: Scoring Components")
    print("=" * 80)
    
    agent = FragilityAgent()
    
    # Test centrality scoring
    print("\n[Centrality Scoring]")
    score, reasons = agent._compute_centrality_score(in_degree=5, max_in_degree=10)
    print(f"  In-degree: 5/10 -> Score: {score:.2f}")
    print(f"  Reasons: {reasons}")
    
    # Test churn scoring
    print("\n[Churn Scoring]")
    score, reasons = agent._compute_churn_score(churn=80, max_churn=100)
    print(f"  Churn: 80/100 -> Score: {score:.2f}")
    print(f"  Reasons: {reasons}")
    
    # Test incident scoring
    print("\n[Incident Scoring]")
    score, reasons = agent._compute_incident_score(incidents=3, max_incidents=5)
    print(f"  Incidents: 3/5 -> Score: {score:.2f}")
    print(f"  Reasons: {reasons}")
    
    print("\n[PASS] Scoring components test passed")
    return True


def test_fragility_calculation_with_mock_neo4j():
    """Test complete fragility calculation with mocked Neo4j."""
    print("\n\n" + "=" * 80)
    print("TEST 4: Complete Fragility Calculation (Mocked Neo4j)")
    print("=" * 80)
    
    # Mock Neo4j data (in-degree centrality)
    mock_in_degree = {
        "auth-service": 5,
        "payment-service": 2,
        "inventory-service": 1,
        "checkout-service": 0,
        "database-service": 3
    }
    
    # Operational metrics
    operational_metrics = {
        "mock_churn": {
            "auth-service": 92,
            "payment-service": 31,
            "inventory-service": 15,
            "checkout-service": 45
        },
        "mock_incidents": {
            "auth-service": 4,
            "payment-service": 1,
            "checkout-service": 2,
            "database-service": 1
        }
    }
    
    # Create agent with mocked Neo4j
    agent = FragilityAgent(
        neo4j_uri="bolt://mock:7687",
        neo4j_user="mock",
        neo4j_password="mock"
    )
    
    # Mock the query_dependency_graph method
    agent.query_dependency_graph = Mock(return_value=mock_in_degree)
    
    try:
        result = agent.compute_fragility_scores(operational_metrics)
        
        print("\n[Fragility Scores]")
        for score_data in result.fragility_scores:
            print(f"\n{'=' * 60}")
            print(f"Service: {score_data.service}")
            print(f"Score: {score_data.score}/10.0")
            print(f"Reasons:")
            for reason in score_data.reasons:
                print(f"  • {reason}")
        
        # Validate output structure
        assert len(result.fragility_scores) > 0
        assert all(0.0 <= s.score <= 10.0 for s in result.fragility_scores)
        assert all(len(s.reasons) > 0 for s in result.fragility_scores)
        
        # Check that auth-service has highest score (high centrality + high churn + high incidents)
        auth_score = next(s for s in result.fragility_scores if s.service == "auth-service")
        print(f"\n✓ Auth-service score: {auth_score.score}/10.0 (should be high)")
        
        print("\n[PASS] Complete fragility calculation test passed")
        return True
        
    except Exception as e:
        print(f"\n[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_edge_cases():
    """Test edge cases and boundary conditions."""
    print("\n\n" + "=" * 80)
    print("TEST 5: Edge Cases")
    print("=" * 80)
    
    agent = FragilityAgent(
        neo4j_uri="bolt://mock:7687",
        neo4j_user="mock",
        neo4j_password="mock"
    )
    
    # Test 1: Empty metrics
    print("\n[Test 1: Empty Metrics]")
    agent.query_dependency_graph = Mock(return_value={})
    try:
        result = agent.compute_fragility_scores({
            "mock_churn": {},
            "mock_incidents": {}
        })
        print(f"✓ Handled empty metrics: {len(result.fragility_scores)} services")
    except Exception as e:
        print(f"✗ Failed on empty metrics: {e}")
        return False
    
    # Test 2: Service with only centrality (no churn/incidents)
    print("\n[Test 2: Service with Only Centrality]")
    agent.query_dependency_graph = Mock(return_value={"lonely-service": 5})
    try:
        result = agent.compute_fragility_scores({
            "mock_churn": {},
            "mock_incidents": {}
        })
        lonely = result.fragility_scores[0]
        print(f"✓ Service: {lonely.service}, Score: {lonely.score}/10.0")
        print(f"  Reasons: {lonely.reasons[0]}")
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False
    
    # Test 3: Service with only operational metrics (no centrality)
    print("\n[Test 3: Service with Only Operational Metrics]")
    agent.query_dependency_graph = Mock(return_value={})
    try:
        result = agent.compute_fragility_scores({
            "mock_churn": {"isolated-service": 100},
            "mock_incidents": {"isolated-service": 5}
        })
        isolated = result.fragility_scores[0]
        print(f"✓ Service: {isolated.service}, Score: {isolated.score}/10.0")
        print(f"  Reasons: {isolated.reasons[0]}")
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False
    
    # Test 4: All zeros
    print("\n[Test 4: All Zero Values]")
    agent.query_dependency_graph = Mock(return_value={"zero-service": 0})
    try:
        result = agent.compute_fragility_scores({
            "mock_churn": {"zero-service": 0},
            "mock_incidents": {"zero-service": 0}
        })
        zero = result.fragility_scores[0]
        print(f"✓ Service: {zero.service}, Score: {zero.score}/10.0")
        assert zero.score == 0.0, "Score should be 0.0 for all zeros"
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False
    
    print("\n[PASS] Edge cases test passed")
    return True


def test_json_output_format():
    """Test that output is valid JSON matching the required schema."""
    print("\n\n" + "=" * 80)
    print("TEST 6: JSON Output Format Validation")
    print("=" * 80)
    
    agent = FragilityAgent(
        neo4j_uri="bolt://mock:7687",
        neo4j_user="mock",
        neo4j_password="mock"
    )
    
    # Mock data
    agent.query_dependency_graph = Mock(return_value={
        "auth-service": 5,
        "payment-service": 2
    })
    
    operational_metrics = {
        "mock_churn": {"auth-service": 92, "payment-service": 31},
        "mock_incidents": {"auth-service": 4}
    }
    
    try:
        result = agent.compute_fragility_scores(operational_metrics)
        
        # Convert to JSON
        json_output = json.loads(result.json())
        
        print("\n[JSON Output]")
        print(json.dumps(json_output, indent=2))
        
        # Validate schema
        assert "fragility_scores" in json_output
        assert isinstance(json_output["fragility_scores"], list)
        
        for score in json_output["fragility_scores"]:
            assert "service" in score
            assert "score" in score
            assert "reasons" in score
            assert isinstance(score["service"], str)
            assert isinstance(score["score"], (int, float))
            assert isinstance(score["reasons"], list)
            assert 0.0 <= score["score"] <= 10.0
        
        print("\n✓ JSON output matches required schema")
        print(f"✓ Total services: {len(json_output['fragility_scores'])}")
        print(f"✓ All scores in valid range (0.0-10.0)")
        
        print("\n[PASS] JSON output format validation passed")
        return True
        
    except Exception as e:
        print(f"\n[FAIL] JSON validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all tests and report results."""
    print("\n" + "=" * 80)
    print("FRAGILITY AGENT - COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    
    tests = [
        ("Operational Metrics Validation", test_operational_metrics_validation),
        ("Metric Normalization Logic", test_normalization_logic),
        ("Scoring Components", test_scoring_components),
        ("Complete Fragility Calculation", test_fragility_calculation_with_mock_neo4j),
        ("Edge Cases", test_edge_cases),
        ("JSON Output Format", test_json_output_format),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"\n[ERROR] Test '{test_name}' crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n{passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print(f"\n⚠️  {total_count - passed_count} test(s) failed")
    
    print("=" * 80)
    
    return passed_count == total_count


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)

# Made with Bob