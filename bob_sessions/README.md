# Fragility Agent

## Overview

The **Fragility Agent** is a specialized component of the IncidentOS AI Engine that analyzes microservice fragility by combining structural graph metrics from Neo4j with operational metrics (code churn and incident frequency). It computes normalized fragility scores (0.0 - 10.0) and provides concrete, actionable risk reasons for each service.

## Purpose

In a microservices architecture, understanding which services are most fragile is critical for:
- **Proactive Risk Management**: Identify services that need immediate attention
- **Resource Allocation**: Focus engineering efforts on high-risk areas
- **Incident Prevention**: Reduce cascading failures by addressing fragile dependencies
- **Architectural Decisions**: Make informed choices about service refactoring

## Key Features

- ✅ **Neo4j Integration**: Queries dependency graph for in-degree centrality (blast radius)
- ✅ **Multi-Factor Scoring**: Combines structural and operational metrics
- ✅ **Normalized Scores**: 0.0 (perfectly safe) to 10.0 (extremely fragile)
- ✅ **Actionable Insights**: Provides specific reasons for each risk score
- ✅ **Flexible Weighting**: Configurable weights for different risk factors
- ✅ **Pure JSON Output**: Structured output for easy integration

## Architecture

### Input Schema

```json
{
  "mock_churn": {
    "service-name": <int>,  // Number of commits/changes
    ...
  },
  "mock_incidents": {
    "service-name": <int>,  // Number of incidents
    ...
  }
}
```

### Output Schema

```json
{
  "fragility_scores": [
    {
      "service": "string",
      "score": 0.0-10.0,
      "reasons": [
        "string describing risk factors"
      ]
    }
  ]
}
```

## Scoring Algorithm

### Components (Weighted)

1. **Centrality Score (50%)**: Based on in-degree from Neo4j
   - High in-degree = High blast radius = Higher fragility
   - Services with many dependents are critical hubs

2. **Churn Score (25%)**: Based on code change frequency
   - High churn = More instability = Higher fragility
   - Frequent changes increase bug introduction risk

3. **Incident Score (25%)**: Based on historical incidents
   - High incidents = Operational instability = Higher fragility
   - Past failures predict future failures

### Formula

```
final_score = (
    centrality_normalized * 0.50 +
    churn_normalized * 0.25 +
    incidents_normalized * 0.25
) * 10.0
```

### Risk Levels

| Score Range | Risk Level | Description |
|-------------|-----------|-------------|
| 8.0 - 10.0 | ⚠️ CRITICAL | Immediate attention required |
| 6.0 - 7.9 | ⚠️ HIGH | Requires monitoring and mitigation |
| 4.0 - 5.9 | ⚠️ MODERATE | Consider improvements |
| 2.0 - 3.9 | ✓ LOW | Generally stable |
| 0.0 - 1.9 | ✓ MINIMAL | Very stable |

## Installation

### Prerequisites

1. **Neo4j Database**: Running instance with populated dependency data
2. **Python 3.8+**: With required packages
3. **Dependencies**: Install via requirements.txt

```bash
pip install -r requirements.txt
```

### Required Packages

- `neo4j>=5.25.0`: Neo4j Python driver
- `pydantic>=2.9.2`: Data validation

## Usage

### Basic Usage

```python
from fragility_agent import FragilityAgent

# Operational metrics
metrics = {
    "mock_churn": {
        "auth-service": 92,
        "payment-service": 31
    },
    "mock_incidents": {
        "auth-service": 4,
        "payment-service": 1
    }
}

# Create agent
agent = FragilityAgent(
    neo4j_uri="bolt://localhost:7687",
    neo4j_user="neo4j",
    neo4j_password="password"
)

# Analyze
result = agent.analyze(metrics)
print(result)
```

### Convenience Function

```python
from fragility_agent import analyze_fragility

result = analyze_fragility(
    operational_metrics=metrics,
    neo4j_uri="bolt://localhost:7687",
    neo4j_user="neo4j",
    neo4j_password="password"
)
```

### Environment Variables

```bash
export NEO4J_URI="bolt://localhost:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="your_password"
```

## Example Output

```json
{
  "fragility_scores": [
    {
      "service": "auth-service",
      "score": 8.7,
      "reasons": [
        "⚠️ CRITICAL RISK: Immediate attention required",
        "Critical hub: 5 services depend on this (high blast radius)",
        "Very high code churn: 92 changes (increased instability risk)",
        "Frequent incidents: 4 incidents (operational instability)"
      ]
    },
    {
      "service": "payment-service",
      "score": 4.2,
      "reasons": [
        "⚠️ MODERATE RISK: Consider improvements",
        "Moderate dependency hub: 2 services depend on this",
        "Moderate code churn: 31 changes",
        "Low incident rate: 1 incidents"
      ]
    }
  ]
}
```

## Integration Workflow

### Step 1: Populate Neo4j

Use the Dependency Agent to populate Neo4j with service dependencies:

```python
from dependency_agent import DependencyGraphManager

manager = DependencyGraphManager(
    neo4j_uri="bolt://localhost:7687",
    neo4j_user="neo4j",
    neo4j_password="password"
)

# Process and execute
result = manager.process(dependency_data, dry_run=False)
```

### Step 2: Gather Operational Metrics

Collect churn and incident data from your systems:

```python
operational_metrics = {
    "mock_churn": get_commit_counts(),      # From Git
    "mock_incidents": get_incident_counts()  # From incident tracking
}
```

### Step 3: Run Fragility Analysis

```python
from fragility_agent import FragilityAgent

agent = FragilityAgent(
    neo4j_uri="bolt://localhost:7687",
    neo4j_user="neo4j",
    neo4j_password="password"
)

fragility_report = agent.analyze(operational_metrics)
```

### Step 4: Act on Results

```python
# Filter high-risk services
high_risk = [
    s for s in fragility_report["fragility_scores"]
    if s["score"] >= 6.0
]

# Prioritize remediation
for service in high_risk:
    print(f"Action needed for: {service['service']}")
    print(f"Score: {service['score']}")
    for reason in service['reasons']:
        print(f"  - {reason}")
```

## Configuration

### Adjusting Weights

Modify the weights in `FragilityAgent.__init__()`:

```python
self.WEIGHT_CENTRALITY = 0.50  # 50% weight to graph structure
self.WEIGHT_CHURN = 0.25       # 25% weight to code churn
self.WEIGHT_INCIDENTS = 0.25   # 25% weight to incidents
```

**Note**: Weights must sum to 1.0

### Custom Thresholds

The agent uses dynamic thresholds based on dataset statistics. To customize:

1. Modify `_compute_centrality_score()` for centrality thresholds
2. Modify `_compute_churn_score()` for churn thresholds
3. Modify `_compute_incident_score()` for incident thresholds

## Testing

### Run Example Script

```bash
cd ai-engine/agents/fragility_agent
python fragility_agent.py
```

### Run Example Usage

```bash
python example_usage.py
```

### Unit Tests

```bash
pytest tests/test_fragility_agent.py
```

## Neo4j Query Details

The agent executes the following Cypher query to retrieve in-degree centrality:

```cypher
MATCH (s:Service)
OPTIONAL MATCH (dependent:Service)-[:DEPENDS_ON]->(s)
WITH s.name AS service, COUNT(dependent) AS in_degree
RETURN service, in_degree
ORDER BY in_degree DESC
```

This query:
1. Matches all Service nodes
2. Counts how many services depend on each service
3. Returns the in-degree (dependency count) for each service

## Error Handling

The agent handles common errors gracefully:

- **Neo4j Connection Failure**: Raises `RuntimeError` with connection details
- **Missing Credentials**: Raises `ValueError` if URI/user/password not provided
- **Invalid Input**: Pydantic validation errors for malformed input
- **Query Failures**: Captures and reports Neo4j query errors

## Performance Considerations

- **Neo4j Connection**: Opens and closes connection per analysis
- **Normalization**: O(n) where n = number of services
- **Scoring**: O(n) computation for all services
- **Memory**: Minimal - processes services sequentially

For large graphs (>1000 services), consider:
- Connection pooling
- Batch processing
- Caching normalized values

## Limitations

1. **Static Weights**: Weights are fixed at initialization
2. **Linear Normalization**: Uses min-max normalization (may not suit all distributions)
3. **No Historical Trending**: Analyzes current state only
4. **Mock Data**: Designed for mock churn/incident data (extend for real sources)

## Future Enhancements

- [ ] Dynamic weight adjustment based on context
- [ ] Historical trend analysis
- [ ] Integration with Git history agent for real churn data
- [ ] Integration with incident tracking systems
- [ ] Machine learning-based scoring
- [ ] Predictive failure modeling
- [ ] Automated remediation suggestions

## Troubleshooting

### "Failed to connect to Neo4j"

**Solution**: Verify Neo4j is running and credentials are correct

```bash
# Test Neo4j connection
cypher-shell -u neo4j -p password
```

### "No services found in Neo4j"

**Solution**: Populate Neo4j using the Dependency Agent first

```bash
python dependency_agent/dependency_graph_manager.py
```

### "Type validation error"

**Solution**: Ensure input matches the expected schema

```python
# Correct format
{
    "mock_churn": {"service-name": 10},
    "mock_incidents": {"service-name": 2}
}
```

## Contributing

When extending the Fragility Agent:

1. Maintain backward compatibility with output schema
2. Add comprehensive docstrings
3. Include unit tests for new features
4. Update this README with new capabilities

## License

Part of the IncidentOS AI Engine project.

## Contact

For questions or issues, refer to the main IncidentOS documentation.

---

**Made with Bob** 🤖