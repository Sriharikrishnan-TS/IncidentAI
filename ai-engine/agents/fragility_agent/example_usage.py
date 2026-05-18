"""
Example usage of the Fragility Agent.

This script demonstrates how to use the Fragility Agent to analyze
microservice fragility by combining Neo4j dependency data with
operational metrics.
"""

import json
import os
from fragility_agent import FragilityAgent, analyze_fragility


def example_basic_usage():
    """Basic example of using the Fragility Agent."""
    print("=" * 80)
    print("EXAMPLE 1: Basic Fragility Analysis")
    print("=" * 80)
    
    # Mock operational metrics
    operational_metrics = {
        "mock_churn": {
            "auth-service": 92,
            "payment-service": 31,
            "inventory-service": 15,
            "checkout-service": 45,
            "order-service": 28,
            "user-service": 12,
            "notification-service": 8,
            "profile-service": 19,
            "analytics-service": 67
        },
        "mock_incidents": {
            "auth-service": 4,
            "payment-service": 1,
            "checkout-service": 2,
            "analytics-service": 3,
            "database-service": 1
        }
    }
    
    print("\n[INPUT: Operational Metrics]")
    print(json.dumps(operational_metrics, indent=2))
    
    # Get Neo4j credentials from environment
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
    
    try:
        # Create agent and analyze
        agent = FragilityAgent(
            neo4j_uri=neo4j_uri,
            neo4j_user=neo4j_user,
            neo4j_password=neo4j_password
        )
        
        result = agent.analyze(operational_metrics)
        
        print("\n[OUTPUT: Fragility Scores]")
        print(json.dumps(result, indent=2))
        
        # Display top 3 most fragile services
        print("\n[TOP 3 MOST FRAGILE SERVICES]")
        for i, score_data in enumerate(result["fragility_scores"][:3], 1):
            print(f"\n{i}. {score_data['service'].upper()}")
            print(f"   Score: {score_data['score']}/10.0")
            print(f"   Key Risks:")
            for reason in score_data['reasons'][:3]:
                print(f"     • {reason}")
        
        return result
        
    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        print("\nMake sure:")
        print("1. Neo4j is running")
        print("2. Dependency data is populated (run dependency_agent first)")
        print("3. Environment variables are set:")
        print("   NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD")
        return None


def example_convenience_function():
    """Example using the convenience function."""
    print("\n\n" + "=" * 80)
    print("EXAMPLE 2: Using Convenience Function")
    print("=" * 80)
    
    operational_metrics = {
        "mock_churn": {
            "auth-service": 92,
            "payment-service": 31
        },
        "mock_incidents": {
            "auth-service": 4
        }
    }
    
    try:
        result = analyze_fragility(
            operational_metrics=operational_metrics,
            neo4j_uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            neo4j_user=os.getenv("NEO4J_USER", "neo4j"),
            neo4j_password=os.getenv("NEO4J_PASSWORD", "password")
        )
        
        print("\n[RESULT]")
        print(json.dumps(result, indent=2))
        
        return result
        
    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        return None


def example_filtering_high_risk():
    """Example showing how to filter high-risk services."""
    print("\n\n" + "=" * 80)
    print("EXAMPLE 3: Filtering High-Risk Services")
    print("=" * 80)
    
    operational_metrics = {
        "mock_churn": {
            "auth-service": 92,
            "payment-service": 31,
            "inventory-service": 15,
            "checkout-service": 45,
            "order-service": 28,
            "user-service": 12,
            "notification-service": 8,
            "profile-service": 19,
            "analytics-service": 67
        },
        "mock_incidents": {
            "auth-service": 4,
            "payment-service": 1,
            "checkout-service": 2,
            "analytics-service": 3,
            "database-service": 1
        }
    }
    
    try:
        result = analyze_fragility(
            operational_metrics=operational_metrics,
            neo4j_uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            neo4j_user=os.getenv("NEO4J_USER", "neo4j"),
            neo4j_password=os.getenv("NEO4J_PASSWORD", "password")
        )
        
        # Filter services with score >= 6.0 (high risk)
        high_risk_services = [
            s for s in result["fragility_scores"]
            if s["score"] >= 6.0
        ]
        
        print(f"\n[HIGH RISK SERVICES] (Score >= 6.0)")
        print(f"Found {len(high_risk_services)} high-risk services:\n")
        
        for service_data in high_risk_services:
            print(f"{'=' * 60}")
            print(f"Service: {service_data['service']}")
            print(f"Score: {service_data['score']}/10.0")
            print(f"Reasons:")
            for reason in service_data['reasons']:
                print(f"  • {reason}")
            print()
        
        return high_risk_services
        
    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        return None


def example_export_to_json():
    """Example showing how to export results to a JSON file."""
    print("\n\n" + "=" * 80)
    print("EXAMPLE 4: Exporting Results to JSON File")
    print("=" * 80)
    
    operational_metrics = {
        "mock_churn": {
            "auth-service": 92,
            "payment-service": 31,
            "inventory-service": 15
        },
        "mock_incidents": {
            "auth-service": 4,
            "payment-service": 1
        }
    }
    
    try:
        result = analyze_fragility(
            operational_metrics=operational_metrics,
            neo4j_uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            neo4j_user=os.getenv("NEO4J_USER", "neo4j"),
            neo4j_password=os.getenv("NEO4J_PASSWORD", "password")
        )
        
        # Export to JSON file
        output_file = "fragility_analysis_results.json"
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2)
        
        print(f"\n[SUCCESS] Results exported to: {output_file}")
        print(f"Total services analyzed: {len(result['fragility_scores'])}")
        
        return result
        
    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        return None


if __name__ == "__main__":
    print("FRAGILITY AGENT - EXAMPLE USAGE")
    print("=" * 80)
    print("\nThis script demonstrates various ways to use the Fragility Agent.")
    print("\nPrerequisites:")
    print("1. Neo4j database running with dependency data")
    print("2. Environment variables set: NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD")
    print("\n" + "=" * 80)
    
    # Run examples
    example_basic_usage()
    example_convenience_function()
    example_filtering_high_risk()
    example_export_to_json()
    
    print("\n" + "=" * 80)
    print("ALL EXAMPLES COMPLETE")
    print("=" * 80)

# Made with Bob