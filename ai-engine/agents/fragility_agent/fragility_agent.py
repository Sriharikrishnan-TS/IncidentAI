"""
Fragility Agent for IncidentOS AI Engine.

This module analyzes microservice fragility by combining:
1. Structural graph metrics (in-degree centrality from Neo4j)
2. Operational metrics (commit churn and incident frequency)
3. Normalized fragility scoring (0.0 - 10.0 scale)

The agent provides concrete risk reasons for each service.
"""

import json
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict
from pydantic import BaseModel, Field, field_validator


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class OperationalMetrics(BaseModel):
    """Model for operational metrics input."""
    mock_churn: Dict[str, int] = Field(default_factory=dict)
    mock_incidents: Dict[str, int] = Field(default_factory=dict)
    
    @field_validator('mock_churn', 'mock_incidents')
    @classmethod
    def normalize_keys(cls, v: Dict[str, int]) -> Dict[str, int]:
        """Normalize service names to lowercase."""
        return {k.strip().lower(): val for k, val in v.items()}


class FragilityScore(BaseModel):
    """Model for a single service's fragility score."""
    service: str
    score: float = Field(ge=0.0, le=10.0)
    reasons: List[str]


class FragilityOutput(BaseModel):
    """Complete output model for the Fragility Agent."""
    fragility_scores: List[FragilityScore]


# ============================================================================
# FRAGILITY AGENT
# ============================================================================

class FragilityAgent:
    """
    Fragility Agent for microservice risk assessment.
    
    Combines structural graph metrics with operational data to compute
    normalized fragility scores and provide actionable risk insights.
    """
    
    def __init__(self, neo4j_uri: Optional[str] = None,
                 neo4j_user: Optional[str] = None,
                 neo4j_password: Optional[str] = None):
        """
        Initialize the Fragility Agent.
        
        Args:
            neo4j_uri: Neo4j database URI (e.g., "bolt://localhost:7687")
            neo4j_user: Neo4j username
            neo4j_password: Neo4j password
        """
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
        self.driver = None
        
        # Scoring weights (must sum to 1.0)
        self.WEIGHT_CENTRALITY = 0.50  # 50% weight to graph structure
        self.WEIGHT_CHURN = 0.25       # 25% weight to code churn
        self.WEIGHT_INCIDENTS = 0.25   # 25% weight to incident history
    
    def _connect_to_neo4j(self):
        """Establish connection to Neo4j database."""
        if not all([self.neo4j_uri, self.neo4j_user, self.neo4j_password]):
            raise ValueError(
                "Neo4j connection requires uri, user, and password"
            )
        
        # Type narrowing assertions for the type checker
        assert self.neo4j_uri is not None
        assert self.neo4j_user is not None
        assert self.neo4j_password is not None
        
        try:
            from neo4j import GraphDatabase
            self.driver = GraphDatabase.driver(
                self.neo4j_uri,
                auth=(self.neo4j_user, self.neo4j_password)
            )
            # Test connection
            with self.driver.session() as session:
                session.run("RETURN 1")
        except Exception as e:
            raise RuntimeError(f"Failed to connect to Neo4j: {str(e)}") from e
    
    def _close_neo4j(self):
        """Close Neo4j database connection."""
        if self.driver:
            self.driver.close()
            self.driver = None
    
    def query_dependency_graph(self) -> Dict[str, int]:
        """
        Query Neo4j for in-degree centrality (dependency count).
        
        Returns:
            Dictionary mapping service names to their in-degree counts
        """
        if not self.driver:
            self._connect_to_neo4j()
        
        if self.driver is None:
            raise RuntimeError("Failed to initialize Neo4j driver")
        
        query = """
        MATCH (s:Service)
        OPTIONAL MATCH (dependent:Service)-[:DEPENDS_ON]->(s)
        WITH s.name AS service, COUNT(dependent) AS in_degree
        RETURN service, in_degree
        ORDER BY in_degree DESC
        """
        
        in_degree_map = {}
        
        try:
            with self.driver.session() as session:
                result = session.run(query)
                for record in result:
                    service_name = record["service"].strip().lower()
                    in_degree_map[service_name] = record["in_degree"]
        except Exception as e:
            raise RuntimeError(f"Failed to query Neo4j: {str(e)}") from e
        
        return in_degree_map
    
    def _normalize_metric(self, value: float, max_value: float, 
                         min_value: float = 0.0) -> float:
        """
        Normalize a metric to 0.0-1.0 range.
        
        Args:
            value: The value to normalize
            max_value: Maximum value in the dataset
            min_value: Minimum value in the dataset
            
        Returns:
            Normalized value between 0.0 and 1.0
        """
        if max_value == min_value:
            return 0.0
        return (value - min_value) / (max_value - min_value)
    
    def _compute_centrality_score(self, in_degree: int, 
                                  max_in_degree: int) -> Tuple[float, List[str]]:
        """
        Compute centrality component of fragility score.
        
        Args:
            in_degree: Number of services depending on this service
            max_in_degree: Maximum in-degree in the graph
            
        Returns:
            Tuple of (normalized_score, reasons)
        """
        reasons = []
        
        if in_degree == 0:
            reasons.append("Leaf service with no dependents (low blast radius)")
            return 0.0, reasons
        
        normalized = self._normalize_metric(in_degree, max_in_degree)
        
        if in_degree >= max_in_degree * 0.7:
            reasons.append(
                f"Critical hub: {in_degree} services depend on this "
                f"(high blast radius)"
            )
        elif in_degree >= max_in_degree * 0.4:
            reasons.append(
                f"Moderate dependency hub: {in_degree} services depend on this"
            )
        elif in_degree > 0:
            reasons.append(
                f"Low dependency count: {in_degree} services depend on this"
            )
        
        return normalized, reasons
    
    def _compute_churn_score(self, churn: int, 
                            max_churn: int) -> Tuple[float, List[str]]:
        """
        Compute churn component of fragility score.
        
        Args:
            churn: Commit/change frequency for this service
            max_churn: Maximum churn in the dataset
            
        Returns:
            Tuple of (normalized_score, reasons)
        """
        reasons = []
        
        if churn == 0:
            reasons.append("No recent code changes (stable)")
            return 0.0, reasons
        
        normalized = self._normalize_metric(churn, max_churn)
        
        if churn >= max_churn * 0.7:
            reasons.append(
                f"Very high code churn: {churn} changes "
                f"(increased instability risk)"
            )
        elif churn >= max_churn * 0.4:
            reasons.append(
                f"Moderate code churn: {churn} changes"
            )
        elif churn > 0:
            reasons.append(
                f"Low code churn: {churn} changes"
            )
        
        return normalized, reasons
    
    def _compute_incident_score(self, incidents: int,
                               max_incidents: int) -> Tuple[float, List[str]]:
        """
        Compute incident component of fragility score.
        
        Args:
            incidents: Number of incidents for this service
            max_incidents: Maximum incidents in the dataset
            
        Returns:
            Tuple of (normalized_score, reasons)
        """
        reasons = []
        
        if incidents == 0:
            reasons.append("No recent incidents (reliable)")
            return 0.0, reasons
        
        normalized = self._normalize_metric(incidents, max_incidents)
        
        if incidents >= max_incidents * 0.7:
            reasons.append(
                f"Frequent incidents: {incidents} incidents "
                f"(operational instability)"
            )
        elif incidents >= max_incidents * 0.4:
            reasons.append(
                f"Moderate incident rate: {incidents} incidents"
            )
        elif incidents > 0:
            reasons.append(
                f"Low incident rate: {incidents} incidents"
            )
        
        return normalized, reasons
    
    def compute_fragility_scores(self, 
                                operational_metrics: Dict[str, Any]) -> FragilityOutput:
        """
        Compute fragility scores for all services.
        
        Args:
            operational_metrics: Dictionary with mock_churn and mock_incidents
            
        Returns:
            FragilityOutput with scores and reasons for each service
        """
        # Validate and normalize input
        metrics = OperationalMetrics(**operational_metrics)
        
        # Query Neo4j for dependency graph
        in_degree_map = self.query_dependency_graph()
        
        # Collect all unique services
        all_services = set(in_degree_map.keys())
        all_services.update(metrics.mock_churn.keys())
        all_services.update(metrics.mock_incidents.keys())
        
        # Calculate max values for normalization
        max_in_degree = max(in_degree_map.values()) if in_degree_map else 1
        max_churn = max(metrics.mock_churn.values()) if metrics.mock_churn else 1
        max_incidents = max(metrics.mock_incidents.values()) if metrics.mock_incidents else 1
        
        # Compute scores for each service
        fragility_scores = []
        
        for service in sorted(all_services):
            # Get metrics (default to 0 if not present)
            in_degree = in_degree_map.get(service, 0)
            churn = metrics.mock_churn.get(service, 0)
            incidents = metrics.mock_incidents.get(service, 0)
            
            # Compute component scores
            centrality_score, centrality_reasons = self._compute_centrality_score(
                in_degree, max_in_degree
            )
            churn_score, churn_reasons = self._compute_churn_score(
                churn, max_churn
            )
            incident_score, incident_reasons = self._compute_incident_score(
                incidents, max_incidents
            )
            
            # Weighted combination (scale to 0-10)
            final_score = (
                centrality_score * self.WEIGHT_CENTRALITY +
                churn_score * self.WEIGHT_CHURN +
                incident_score * self.WEIGHT_INCIDENTS
            ) * 10.0
            
            # Round to one decimal place
            final_score = round(final_score, 1)
            
            # Combine reasons
            all_reasons = centrality_reasons + churn_reasons + incident_reasons
            
            # Add risk level summary
            if final_score >= 8.0:
                all_reasons.insert(0, "⚠️ CRITICAL RISK: Immediate attention required")
            elif final_score >= 6.0:
                all_reasons.insert(0, "⚠️ HIGH RISK: Requires monitoring and mitigation")
            elif final_score >= 4.0:
                all_reasons.insert(0, "⚠️ MODERATE RISK: Consider improvements")
            elif final_score >= 2.0:
                all_reasons.insert(0, "✓ LOW RISK: Generally stable")
            else:
                all_reasons.insert(0, "✓ MINIMAL RISK: Very stable")
            
            fragility_scores.append(FragilityScore(
                service=service,
                score=final_score,
                reasons=all_reasons
            ))
        
        # Sort by score (highest risk first)
        fragility_scores.sort(key=lambda x: x.score, reverse=True)
        
        return FragilityOutput(fragility_scores=fragility_scores)
    
    def analyze(self, operational_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point for fragility analysis.
        
        Args:
            operational_metrics: Dictionary with mock_churn and mock_incidents
            
        Returns:
            Dictionary representation of FragilityOutput (pure JSON)
        """
        try:
            result = self.compute_fragility_scores(operational_metrics)
            return json.loads(result.json())
        finally:
            self._close_neo4j()


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================

def analyze_fragility(operational_metrics: Dict[str, Any],
                     neo4j_uri: str,
                     neo4j_user: str,
                     neo4j_password: str) -> Dict[str, Any]:
    """
    Convenience function for fragility analysis.
    
    Args:
        operational_metrics: Dictionary with mock_churn and mock_incidents
        neo4j_uri: Neo4j database URI
        neo4j_user: Neo4j username
        neo4j_password: Neo4j password
        
    Returns:
        Dictionary with fragility scores (pure JSON)
    """
    agent = FragilityAgent(
        neo4j_uri=neo4j_uri,
        neo4j_user=neo4j_user,
        neo4j_password=neo4j_password
    )
    return agent.analyze(operational_metrics)


# ============================================================================
# MAIN EXECUTION WITH MOCK DATA
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("FRAGILITY AGENT - MICROSERVICE RISK ASSESSMENT")
    print("=" * 80)
    
    # Mock operational metrics
    mock_metrics = {
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
    
    print("\n[INPUT: OPERATIONAL METRICS]")
    print(json.dumps(mock_metrics, indent=2))
    
    print("\n[PROCESSING...]")
    print("Note: This requires a running Neo4j instance with populated data.")
    print("Set NEO4J_URI, NEO4J_USER, and NEO4J_PASSWORD environment variables.")
    
    # Example usage (requires Neo4j connection)
    import os
    
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
    
    try:
        agent = FragilityAgent(
            neo4j_uri=neo4j_uri,
            neo4j_user=neo4j_user,
            neo4j_password=neo4j_password
        )
        
        result = agent.analyze(mock_metrics)
        
        print("\n" + "=" * 80)
        print("FRAGILITY ANALYSIS RESULTS")
        print("=" * 80)
        
        print("\n[FRAGILITY SCORES - Ranked by Risk]")
        for score_data in result["fragility_scores"]:
            print(f"\n{'=' * 60}")
            print(f"Service: {score_data['service']}")
            print(f"Score: {score_data['score']}/10.0")
            print(f"Reasons:")
            for reason in score_data['reasons']:
                print(f"  • {reason}")
        
        print("\n" + "=" * 80)
        print("COMPLETE JSON OUTPUT")
        print("=" * 80)
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        print("\nTo run this example:")
        print("1. Start Neo4j database")
        print("2. Populate it with dependency data (use dependency_agent)")
        print("3. Set environment variables:")
        print("   export NEO4J_URI='bolt://localhost:7687'")
        print("   export NEO4J_USER='neo4j'")
        print("   export NEO4J_PASSWORD='your_password'")
    
    print("\n" + "=" * 80)
    print("EXECUTION COMPLETE")
    print("=" * 80)

# Made with Bob