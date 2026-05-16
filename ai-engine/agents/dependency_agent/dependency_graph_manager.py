"""
Dependency Graph Manager for IncidentOS AI Engine.

This module provides a complete implementation for processing microservice
dependency data, generating Neo4j Cypher queries, and performing architectural
risk analysis.
"""

import json
import sys
from typing import Any, Dict, List, Optional, Set, Tuple
from collections import defaultdict
from pydantic import BaseModel, Field, field_validator

# Set UTF-8 encoding securely across environments
if sys.platform == "win32":
    try:
        # Using getattr avoids Pyright's TextIO type stub restrictions
        reconfig_fn = getattr(sys.stdout, "reconfigure", None)
        if reconfig_fn:
            reconfig_fn(encoding='utf-8', errors='replace')
    except Exception:
        pass

# ============================================================================
# PYDANTIC MODELS FOR INPUT VALIDATION
# ============================================================================

class ServiceInput(BaseModel):
    """Model for a single service with its imports."""
    name: str
    imports: List[str] = Field(default_factory=list)
    
    @field_validator('name')
    @classmethod
    def normalize_name(cls, v: str) -> str:
        """Normalize service name: lowercase and trim spaces."""
        return v.strip().lower()
    
    @field_validator('imports')
    @classmethod
    def normalize_imports(cls, v: List[str]) -> List[str]:
        """Normalize import names: lowercase and trim spaces."""
        return [item.strip().lower() for item in v]


class ServicesInput(BaseModel):
    """Model for the complete input JSON schema."""
    services: List[ServiceInput]


# ============================================================================
# OUTPUT MODELS
# ============================================================================

class ExtractedDependency(BaseModel):
    """Model for extracted dependency relationship."""
    service: str
    depends_on: List[str]


class RiskNode(BaseModel):
    """Model for a node identified in risk analysis."""
    service: str
    reason: str


class RiskAnalysis(BaseModel):
    """Model for complete risk analysis results."""
    high_blast_radius_nodes: List[RiskNode]
    highly_fragile_nodes: List[RiskNode]


class DependencyAgentOutput(BaseModel):
    """Complete output model for the Dependency Agent."""
    extracted_dependencies: List[ExtractedDependency]
    neo4j_cypher_queries: List[str]
    risk_analysis: RiskAnalysis


# ============================================================================
# DEPENDENCY GRAPH MANAGER
# ============================================================================

class DependencyGraphManager:
    """
    Main class for managing microservice dependency graphs.
    
    This class handles:
    - Dependency extraction and normalization
    - Neo4j Cypher query generation
    - Architectural risk analysis
    - Optional Neo4j database connectivity
    """
    
    def __init__(self, neo4j_uri: Optional[str] = None, 
                 neo4j_user: Optional[str] = None,
                 neo4j_password: Optional[str] = None):
        """
        Initialize the Dependency Graph Manager.
        
        Args:
            neo4j_uri: Neo4j database URI (e.g., "bolt://localhost:7687")
            neo4j_user: Neo4j username
            neo4j_password: Neo4j password
        """
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
        self.driver = None
        
        # Internal state
        self.dependency_map: Dict[str, Set[str]] = defaultdict(set)
        self.all_services: Set[str] = set()
        self.in_degree: Dict[str, int] = defaultdict(int)
        self.out_degree: Dict[str, int] = defaultdict(int)
    
    def _connect_to_neo4j(self):
        """Establish connection to Neo4j database."""
        if not all([self.neo4j_uri, self.neo4j_user, self.neo4j_password]):
            raise ValueError(
                "Neo4j connection requires uri, user, and password"
            )
        
        # Explicit type narrowing assertions for the type checker
        assert self.neo4j_uri is not None
        assert self.neo4j_user is not None
        assert self.neo4j_password is not None
        
        try:
            from neo4j import GraphDatabase
            self.driver = GraphDatabase.driver(
                self.neo4j_uri,
                auth=(self.neo4j_user, self.neo4j_password)
            )
            with self.driver.session() as session:
                session.run("RETURN 1")
                
        except Exception as e:
            raise RuntimeError(f"Failed to connect to Neo4j: {str(e)}") from e
    
    def _close_neo4j(self):
        """Close Neo4j database connection."""
        if self.driver:
            self.driver.close()
            self.driver = None
    
    def extract_dependencies(self, input_data: Dict[str, Any]) -> List[ExtractedDependency]:
        """
        Extract and normalize dependencies from input JSON.
        
        Args:
            input_data: Dictionary matching the ServicesInput schema
            
        Returns:
            List of ExtractedDependency objects
        """
        # Validate input
        validated_input = ServicesInput(**input_data)
        
        # Reset internal state
        self.dependency_map.clear()
        self.all_services.clear()
        self.in_degree.clear()
        self.out_degree.clear()
        
        # Extract dependencies
        extracted = []
        
        for service in validated_input.services:
            service_name = service.name
            dependencies = service.imports
            
            # Track all services
            self.all_services.add(service_name)
            self.all_services.update(dependencies)
            
            # Build dependency map
            self.dependency_map[service_name] = set(dependencies)
            
            # Calculate degrees
            self.out_degree[service_name] = len(dependencies)
            for dep in dependencies:
                self.in_degree[dep] += 1
            
            # Create output
            extracted.append(ExtractedDependency(
                service=service_name,
                depends_on=sorted(dependencies)
            ))
        
        # Ensure all services have degree entries
        for service in self.all_services:
            if service not in self.in_degree:
                self.in_degree[service] = 0
            if service not in self.out_degree:
                self.out_degree[service] = 0
        
        return sorted(extracted, key=lambda x: x.service)
    
    def generate_cypher_queries(self) -> List[str]:
        """
        Generate idempotent Neo4j Cypher queries for the dependency graph.
        
        Returns:
            List of Cypher query strings
        """
        queries = []
        
        # Create nodes for all services (including imported ones)
        for service in sorted(self.all_services):
            query = f"MERGE (s:Service {{name: '{service}'}});"
            queries.append(query)
        
        # Create relationships
        for service in sorted(self.dependency_map.keys()):
            for dependency in sorted(self.dependency_map[service]):
                query = (
                    f"MERGE (a:Service {{name: '{service}'}}) "
                    f"MERGE (b:Service {{name: '{dependency}'}}) "
                    f"MERGE (a)-[:DEPENDS_ON]->(b);"
                )
                queries.append(query)
        
        return queries
    
    def analyze_risks(self) -> RiskAnalysis:
        """
        Perform architectural risk analysis on the dependency graph.
        
        Identifies:
        - High blast radius nodes (high in-degree)
        - Fragile nodes (high out-degree)
        
        Uses dynamic thresholds based on graph averages with fallback minimums.
        
        Returns:
            RiskAnalysis object with identified risk nodes
        """
        if not self.all_services:
            return RiskAnalysis(
                high_blast_radius_nodes=[],
                highly_fragile_nodes=[]
            )
        
        # Calculate average degrees
        total_services = len(self.all_services)
        avg_in_degree = sum(self.in_degree.values()) / total_services
        avg_out_degree = sum(self.out_degree.values()) / total_services
        
        # Set thresholds with fallback minimums
        blast_radius_threshold = max(avg_in_degree, 3)
        fragile_threshold = max(avg_out_degree, 3)
        
        # Identify high blast radius nodes
        high_blast_radius = []
        for service, in_deg in self.in_degree.items():
            if in_deg >= blast_radius_threshold:
                dependents = [
                    s for s, deps in self.dependency_map.items()
                    if service in deps
                ]
                reason = (
                    f"Critical dependency: {in_deg} services depend on this "
                    f"(threshold: {blast_radius_threshold:.1f}). "
                    f"Failure would impact: {', '.join(sorted(dependents)[:5])}"
                    f"{'...' if len(dependents) > 5 else ''}."
                )
                high_blast_radius.append(RiskNode(
                    service=service,
                    reason=reason
                ))
        
        # Identify fragile nodes
        highly_fragile = []
        for service, out_deg in self.out_degree.items():
            if out_deg >= fragile_threshold:
                dependencies = sorted(self.dependency_map.get(service, []))
                reason = (
                    f"Highly coupled: depends on {out_deg} services "
                    f"(threshold: {fragile_threshold:.1f}). "
                    f"Dependencies: {', '.join(dependencies[:5])}"
                    f"{'...' if len(dependencies) > 5 else ''}. "
                    f"Vulnerable to cascading failures."
                )
                highly_fragile.append(RiskNode(
                    service=service,
                    reason=reason
                ))
        
        return RiskAnalysis(
            high_blast_radius_nodes=sorted(
                high_blast_radius, 
                key=lambda x: self.in_degree[x.service],
                reverse=True
            ),
            highly_fragile_nodes=sorted(
                highly_fragile,
                key=lambda x: self.out_degree[x.service],
                reverse=True
            )
        )
    
    def execute_cypher_queries(self, queries: List[str]) -> Dict[str, Any]:
        """Execute Cypher queries against Neo4j database."""
        if not self.driver:
            self._connect_to_neo4j()
            
        # Add this line to satisfy the type checker's strict tracking
        if self.driver is None:
            raise RuntimeError("Failed to initialize Neo4j driver connection.")
            
        # Import Query locally to maintain Neo4j as an optional dependency
        from neo4j import Query 
        
        results = {
            "total_queries": len(queries),
            "executed": 0,
            "failed": 0,
            "errors": []
        }
        
        try:
            with self.driver.session() as session:
                for i, query in enumerate(queries):
                    try:
                        # Wrap the string in a Query object to satisfy Pyright
                        # Alternative using typing.cast (Requires importing cast at the top of your file)
                        from typing import cast
                        from typing_extensions import LiteralString # Or typing in Python 3.11+

                        # Inside the loop:
                        session.run(cast(LiteralString, query))
                        results["executed"] += 1
                    except Exception as e:
                        results["failed"] += 1
                        results["errors"].append({
                            "query_index": i,
                            "query": query,
                            "error": str(e)
                        })
        finally:
            self._close_neo4j()
        
        return results
    
    def process(self, input_data: Dict[str, Any], 
                dry_run: bool = True) -> DependencyAgentOutput:
        """
        Complete processing pipeline for dependency analysis.
        
        Args:
            input_data: Dictionary matching ServicesInput schema
            dry_run: If True, generate queries without executing them
            
        Returns:
            DependencyAgentOutput with all results
        """
        # Step 1: Extract dependencies
        extracted_deps = self.extract_dependencies(input_data)
        
        # Step 2: Generate Cypher queries
        cypher_queries = self.generate_cypher_queries()
        
        # Step 3: Analyze risks
        risk_analysis = self.analyze_risks()
        
        # Step 4: Optionally execute queries
        if not dry_run:
            execution_results = self.execute_cypher_queries(cypher_queries)
            print(f"\n[Neo4j Execution Results]")
            print(f"Executed: {execution_results['executed']}/{execution_results['total_queries']}")
            if execution_results['failed'] > 0:
                print(f"Failed: {execution_results['failed']}")
                for error in execution_results['errors'][:3]:
                    print(f"  - Query {error['query_index']}: {error['error']}")
        
        return DependencyAgentOutput(
            extracted_dependencies=extracted_deps,
            neo4j_cypher_queries=cypher_queries,
            risk_analysis=risk_analysis
        )


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def process_dependencies(input_data: Dict[str, Any], 
                        dry_run: bool = True,
                        neo4j_uri: Optional[str] = None,
                        neo4j_user: Optional[str] = None,
                        neo4j_password: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to process dependencies in one call.
    
    Args:
        input_data: Dictionary matching ServicesInput schema
        dry_run: If True, generate queries without executing them
        neo4j_uri: Neo4j database URI (required if dry_run=False)
        neo4j_user: Neo4j username (required if dry_run=False)
        neo4j_password: Neo4j password (required if dry_run=False)
        
    Returns:
        Dictionary representation of DependencyAgentOutput
    """
    manager = DependencyGraphManager(
        neo4j_uri=neo4j_uri,
        neo4j_user=neo4j_user,
        neo4j_password=neo4j_password
    )
    
    result = manager.process(input_data, dry_run=dry_run)
    return json.loads(result.json())


# ============================================================================
# MAIN EXECUTION BLOCK WITH MOCK DATA
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("DEPENDENCY AGENT - MICROSERVICE ARCHITECTURE ANALYSIS")
    print("=" * 80)
    
    # Mock data representing a microservice architecture
    mock_input = {
        "services": [
            {
                "name": "  Checkout-Service  ",  # Test normalization
                "imports": ["Auth-Service", "Payment-Service", "Inventory-Service"]
            },
            {
                "name": "Order-Service",
                "imports": ["Auth-Service", "Checkout-Service", "Notification-Service"]
            },
            {
                "name": "User-Service",
                "imports": ["Auth-Service", "Profile-Service"]
            },
            {
                "name": "Payment-Service",
                "imports": ["Auth-Service", "Billing-Service"]
            },
            {
                "name": "Inventory-Service",
                "imports": ["Database-Service"]
            },
            {
                "name": "Notification-Service",
                "imports": ["Email-Service", "SMS-Service"]
            },
            {
                "name": "Profile-Service",
                "imports": ["Database-Service", "Auth-Service"]
            },
            {
                "name": "Analytics-Service",
                "imports": ["Auth-Service", "Database-Service", "User-Service", "Order-Service"]
            }
        ]
    }
    
    print("\n[INPUT DATA]")
    print(json.dumps(mock_input, indent=2))
    
    # Process dependencies
    print("\n[PROCESSING...]")
    manager = DependencyGraphManager()
    result = manager.process(mock_input, dry_run=True)
    
    # Convert to dictionary for pretty printing
    output = json.loads(result.json())
    
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    
    print("\n[1. EXTRACTED DEPENDENCIES]")
    print(f"Total services identified: {len(output['extracted_dependencies'])}")
    for dep in output['extracted_dependencies']:
        if dep['depends_on']:
            print(f"  * {dep['service']} -> {', '.join(dep['depends_on'])}")
        else:
            print(f"  * {dep['service']} (no dependencies)")
    
    print(f"\n[2. NEO4J CYPHER QUERIES]")
    print(f"Total queries generated: {len(output['neo4j_cypher_queries'])}")
    print("\nSample queries:")
    for query in output['neo4j_cypher_queries'][:5]:
        print(f"  {query}")
    if len(output['neo4j_cypher_queries']) > 5:
        print(f"  ... and {len(output['neo4j_cypher_queries']) - 5} more queries")
    
    print(f"\n[3. RISK ANALYSIS]")
    
    print(f"\n[!] HIGH BLAST RADIUS NODES ({len(output['risk_analysis']['high_blast_radius_nodes'])} found):")
    if output['risk_analysis']['high_blast_radius_nodes']:
        for node in output['risk_analysis']['high_blast_radius_nodes']:
            print(f"\n  Service: {node['service']}")
            print(f"  Reason: {node['reason']}")
    else:
        print("  None identified")
    
    print(f"\n[#] HIGHLY FRAGILE NODES ({len(output['risk_analysis']['highly_fragile_nodes'])} found):")
    if output['risk_analysis']['highly_fragile_nodes']:
        for node in output['risk_analysis']['highly_fragile_nodes']:
            print(f"\n  Service: {node['service']}")
            print(f"  Reason: {node['reason']}")
    else:
        print("  None identified")
    
    print("\n" + "=" * 80)
    print("COMPLETE JSON OUTPUT")
    print("=" * 80)
    print(json.dumps(output, indent=2))
    
    print("\n" + "=" * 80)
    print("EXECUTION COMPLETE")
    print("=" * 80)
    print("\nTo execute queries against Neo4j, set dry_run=False and provide:")
    print("  - neo4j_uri (e.g., 'bolt://localhost:7687')")
    print("  - neo4j_user")
    print("  - neo4j_password")

# Made with Bob
