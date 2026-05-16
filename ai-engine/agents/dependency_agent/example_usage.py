"""
Example usage patterns for the Dependency Agent.

This script demonstrates various ways to use the DependencyGraphManager
for analyzing microservice dependencies.
"""

import json
from dependency_graph_manager import (
    DependencyGraphManager,
    process_dependencies,
)


def example_1_basic_usage():
    """Example 1: Basic usage with dry run (no database)."""
    print("=" * 80)
    print("EXAMPLE 1: Basic Usage (Dry Run)")
    print("=" * 80)
    
    input_data = {
        "services": [
            {
                "name": "api-gateway",
                "imports": ["auth-service", "user-service"]
            },
            {
                "name": "user-service",
                "imports": ["database-service"]
            },
            {
                "name": "auth-service",
                "imports": ["database-service", "cache-service"]
            }
        ]
    }
    
    manager = DependencyGraphManager()
    result = manager.process(input_data, dry_run=True)
    
    print(f"\nExtracted {len(result.extracted_dependencies)} dependencies")
    print(f"Generated {len(result.neo4j_cypher_queries)} Cypher queries")
    print(f"Found {len(result.risk_analysis.high_blast_radius_nodes)} high blast radius nodes")
    print(f"Found {len(result.risk_analysis.highly_fragile_nodes)} fragile nodes")
    
    return result


def example_2_convenience_function():
    """Example 2: Using the convenience function."""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Using Convenience Function")
    print("=" * 80)
    
    input_data = {
        "services": [
            {
                "name": "Frontend",
                "imports": ["API-Gateway"]
            },
            {
                "name": "API-Gateway",
                "imports": ["Auth", "Orders", "Products"]
            },
            {
                "name": "Orders",
                "imports": ["Database", "Payment"]
            },
            {
                "name": "Products",
                "imports": ["Database", "Inventory"]
            }
        ]
    }
    
    result = process_dependencies(input_data, dry_run=True)
    
    print("\nRisk Analysis Summary:")
    if result['risk_analysis']['high_blast_radius_nodes']:
        print("\nCritical Services (High Blast Radius):")
        for node in result['risk_analysis']['high_blast_radius_nodes']:
            print(f"  - {node['service']}")
    
    if result['risk_analysis']['highly_fragile_nodes']:
        print("\nFragile Services (High Coupling):")
        for node in result['risk_analysis']['highly_fragile_nodes']:
            print(f"  - {node['service']}")
    
    return result


def example_3_step_by_step():
    """Example 3: Step-by-step processing."""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Step-by-Step Processing")
    print("=" * 80)
    
    input_data = {
        "services": [
            {
                "name": "Mobile-App",
                "imports": ["API-Gateway", "Push-Service"]
            },
            {
                "name": "Web-App",
                "imports": ["API-Gateway"]
            },
            {
                "name": "API-Gateway",
                "imports": ["Auth", "Business-Logic"]
            },
            {
                "name": "Business-Logic",
                "imports": ["Database", "Cache", "Queue"]
            }
        ]
    }
    
    manager = DependencyGraphManager()
    
    # Step 1: Extract dependencies
    print("\nStep 1: Extracting dependencies...")
    dependencies = manager.extract_dependencies(input_data)
    print(f"  Extracted {len(dependencies)} service dependencies")
    
    # Step 2: Generate Cypher queries
    print("\nStep 2: Generating Neo4j Cypher queries...")
    queries = manager.generate_cypher_queries()
    print(f"  Generated {len(queries)} queries")
    print(f"  Sample: {queries[0]}")
    
    # Step 3: Analyze risks
    print("\nStep 3: Analyzing architectural risks...")
    risks = manager.analyze_risks()
    print(f"  High blast radius nodes: {len(risks.high_blast_radius_nodes)}")
    print(f"  Highly fragile nodes: {len(risks.highly_fragile_nodes)}")
    
    if risks.high_blast_radius_nodes:
        print("\n  Most critical service:")
        top_risk = risks.high_blast_radius_nodes[0]
        print(f"    {top_risk.service}")
        print(f"    {top_risk.reason[:100]}...")
    
    return dependencies, queries, risks


def example_4_json_output():
    """Example 4: Working with JSON output."""
    print("\n" + "=" * 80)
    print("EXAMPLE 4: JSON Output Format")
    print("=" * 80)
    
    input_data = {
        "services": [
            {
                "name": "Service-A",
                "imports": ["Service-B", "Service-C"]
            },
            {
                "name": "Service-B",
                "imports": ["Service-D"]
            }
        ]
    }
    
    manager = DependencyGraphManager()
    result = manager.process(input_data, dry_run=True)
    
    # Convert to JSON
    json_output = json.loads(result.json())
    
    print("\nJSON Output Structure:")
    print(json.dumps(json_output, indent=2))
    
    return json_output


def example_5_normalization():
    """Example 5: Demonstrating name normalization."""
    print("\n" + "=" * 80)
    print("EXAMPLE 5: Name Normalization")
    print("=" * 80)
    
    # Input with various naming styles
    input_data = {
        "services": [
            {
                "name": "  User-Service  ",  # Extra spaces
                "imports": ["AUTH-SERVICE", "Database-Service"]  # Mixed case
            },
            {
                "name": "Auth-Service",
                "imports": ["  database-service  "]  # Spaces in imports
            }
        ]
    }
    
    print("\nOriginal input (with inconsistent naming):")
    print(json.dumps(input_data, indent=2))
    
    manager = DependencyGraphManager()
    result = manager.process(input_data, dry_run=True)
    
    print("\nNormalized output:")
    for dep in result.extracted_dependencies:
        print(f"  {dep.service} -> {dep.depends_on}")
    
    return result


if __name__ == "__main__":
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "DEPENDENCY AGENT USAGE EXAMPLES" + " " * 27 + "║")
    print("╚" + "=" * 78 + "╝")
    
    # Run all examples
    example_1_basic_usage()
    example_2_convenience_function()
    example_3_step_by_step()
    example_4_json_output()
    example_5_normalization()
    
    print("\n" + "=" * 80)
    print("ALL EXAMPLES COMPLETED SUCCESSFULLY")
    print("=" * 80)
    print("\nFor Neo4j database integration, provide connection details:")
    print("  manager = DependencyGraphManager(")
    print("      neo4j_uri='bolt://localhost:7687',")
    print("      neo4j_user='neo4j',")
    print("      neo4j_password='your_password'")
    print("  )")
    print("  result = manager.process(input_data, dry_run=False)")
    print()

# Made with Bob
