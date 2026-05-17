# Dependency Agent

A production-ready Python module for analyzing microservice dependency graphs, generating Neo4j Cypher queries, and performing architectural risk analysis.

## Features

- **Dependency Extraction**: Parses and normalizes microservice dependency data
- **Neo4j Integration**: Generates idempotent Cypher queries with optional database execution
- **Risk Analysis**: Identifies high blast radius and fragile nodes using dynamic thresholds
- **Type Safety**: Full Pydantic validation for inputs and outputs
- **Flexible Execution**: Supports both dry-run (query generation) and live database modes

## Installation

```bash
cd ai-engine
pip install -r requirements.txt
```

## Quick Start

### Basic Usage (Dry Run)

```python
from agents.dependency_agent import DependencyGraphManager

# Input data
input_data = {
    "services": [
        {
            "name": "checkout-service",
            "imports": ["auth-service", "payment-service"]
        },
        {
            "name": "order-service",
            "imports": ["auth-service", "checkout-service"]
        }
    ]
}

# Process dependencies
manager = DependencyGraphManager()
result = manager.process(input_data, dry_run=True)

# Access results
print(result.extracted_dependencies)
print(result.neo4j_cypher_queries)
print(result.risk_analysis)
```

### With Neo4j Database Execution

```python
manager = DependencyGraphManager(
    neo4j_uri="bolt://localhost:7687",
    neo4j_user="neo4j",
    neo4j_password="your_password"
)

result = manager.process(input_data, dry_run=False)
```

### Using Convenience Function

```python
from agents.dependency_agent import process_dependencies

result = process_dependencies(
    input_data,
    dry_run=True
)
```

## Input Schema

```json
{
  "services": [
    {
      "name": "string",
      "imports": ["string"]
    }
  ]
}
```

- Service names and imports are automatically normalized (lowercase, trimmed)
- Services referenced in imports but not defined will still be created as nodes

## Output Schema

```json
{
  "extracted_dependencies": [
    {
      "service": "checkout-service",
      "depends_on": ["auth-service", "payment-service"]
    }
  ],
  "neo4j_cypher_queries": [
    "MERGE (s:Service {name: 'checkout-service'});",
    "MERGE (a:Service {name: 'checkout-service'}) MERGE (b:Service {name: 'auth-service'}) MERGE (a)-[:DEPENDS_ON]->(b);"
  ],
  "risk_analysis": {
    "high_blast_radius_nodes": [
      {
        "service": "auth-service",
        "reason": "Critical dependency: 5 services depend on this..."
      }
    ],
    "highly_fragile_nodes": [
      {
        "service": "checkout-service",
        "reason": "Highly coupled: depends on 4 services..."
      }
    ]
  }
}
```

## Risk Analysis

The agent identifies two types of architectural risks:

### High Blast Radius Nodes
Services with many dependents (high in-degree). Failure impacts many services.

**Threshold**: `max(average_in_degree, 3)`

### Highly Fragile Nodes
Services with many dependencies (high out-degree). Vulnerable to cascading failures.

**Threshold**: `max(average_out_degree, 3)`

## Running the Demo

```bash
cd ai-engine/agents/dependency_agent
python dependency_graph_manager.py
```

This will execute the module with comprehensive mock data and display:
- Extracted dependencies
- Generated Cypher queries
- Risk analysis results
- Complete JSON output

## Neo4j Graph Schema

**Nodes**: `:Service` with `name` property

**Relationships**: `(a:Service)-[:DEPENDS_ON]->(b:Service)`

All queries use `MERGE` for idempotency - safe to run multiple times.

## API Reference

### DependencyGraphManager

Main class for dependency graph management.

#### Methods

- `extract_dependencies(input_data)`: Extract and normalize dependencies
- `generate_cypher_queries()`: Generate Neo4j Cypher queries
- `analyze_risks()`: Perform risk analysis
- `execute_cypher_queries(queries)`: Execute queries against Neo4j
- `process(input_data, dry_run=True)`: Complete processing pipeline

### process_dependencies()

Convenience function for one-call processing.

**Parameters**:
- `input_data`: Dictionary matching ServicesInput schema
- `dry_run`: If True, generate queries without executing (default: True)
- `neo4j_uri`: Neo4j database URI (required if dry_run=False)
- `neo4j_user`: Neo4j username (required if dry_run=False)
- `neo4j_password`: Neo4j password (required if dry_run=False)

**Returns**: Dictionary representation of DependencyAgentOutput

## Integration with FastAPI

```python
from fastapi import FastAPI
from agents.dependency_agent import process_dependencies

app = FastAPI()

@app.post("/analyze-dependencies")
async def analyze_dependencies(input_data: dict):
    result = process_dependencies(input_data, dry_run=True)
    return result
```

## Error Handling

The module includes comprehensive error handling:
- Input validation via Pydantic
- Neo4j connection errors
- Query execution errors
- Graceful fallbacks for missing data

## Testing

The module includes a complete test execution block with mock data representing a realistic microservice architecture with 8+ services.

## License

Part of the IncidentOS AI Engine.