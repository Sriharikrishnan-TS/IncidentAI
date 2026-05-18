# Fragility Agent - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Prerequisites

1. **Neo4j Database** running with dependency data
2. **Python 3.8+** installed
3. **Dependencies** installed (see below)

### Installation

```bash
# Install dependencies
cd ai-engine
pip install -r requirements.txt
```

### Step 1: Populate Neo4j with Dependencies

First, use the Dependency Agent to populate Neo4j:

```python
from dependency_agent import DependencyGraphManager

# Your service dependency data
services_data = {
    "services": [
        {
            "name": "checkout-service",
            "imports": ["auth-service", "payment-service", "inventory-service"]
        },
        {
            "name": "order-service",
            "imports": ["auth-service", "checkout-service"]
        }
        # ... more services
    ]
}

# Populate Neo4j
manager = DependencyGraphManager(
    neo4j_uri="bolt://localhost:7687",
    neo4j_user="neo4j",
    neo4j_password="your_password"
)

result = manager.process(services_data, dry_run=False)
print("✓ Neo4j populated with dependencies")
```

### Step 2: Run Fragility Analysis

```python
from fragility_agent import FragilityAgent

# Your operational metrics
metrics = {
    "mock_churn": {
        "auth-service": 92,
        "payment-service": 31,
        "inventory-service": 15,
        "checkout-service": 45
    },
    "mock_incidents": {
        "auth-service": 4,
        "payment-service": 1,
        "checkout-service": 2
    }
}

# Create agent
agent = FragilityAgent(
    neo4j_uri="bolt://localhost:7687",
    neo4j_user="neo4j",
    neo4j_password="your_password"
)

# Analyze fragility
result = agent.analyze(metrics)

# Display results
for service in result["fragility_scores"]:
    print(f"\n{service['service']}: {service['score']}/10.0")
    for reason in service['reasons']:
        print(f"  • {reason}")
```

### Step 3: Act on Results

```python
# Filter high-risk services (score >= 6.0)
high_risk = [
    s for s in result["fragility_scores"]
    if s["score"] >= 6.0
]

print(f"\n⚠️  {len(high_risk)} high-risk services found:")
for service in high_risk:
    print(f"  - {service['service']}: {service['score']}/10.0")
```

## 📊 Example Output

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

## 🧪 Run Tests

```bash
cd ai-engine/agents/fragility_agent
python test_fragility_agent.py
```

Expected output:
```
✓ PASS: Operational Metrics Validation
✓ PASS: Metric Normalization Logic
✓ PASS: Scoring Components
✓ PASS: Complete Fragility Calculation
✓ PASS: Edge Cases
✓ PASS: JSON Output Format

6/6 tests passed
🎉 ALL TESTS PASSED!
```

## 🔧 Configuration

### Adjust Scoring Weights

Edit `fragility_agent.py`:

```python
class FragilityAgent:
    def __init__(self, ...):
        # Customize weights (must sum to 1.0)
        self.WEIGHT_CENTRALITY = 0.50  # Graph structure
        self.WEIGHT_CHURN = 0.25       # Code changes
        self.WEIGHT_INCIDENTS = 0.25   # Incidents
```

### Environment Variables

```bash
export NEO4J_URI="bolt://localhost:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="your_password"
```

Then use:

```python
import os
from fragility_agent import analyze_fragility

result = analyze_fragility(
    operational_metrics=metrics,
    neo4j_uri=os.getenv("NEO4J_URI"),
    neo4j_user=os.getenv("NEO4J_USER"),
    neo4j_password=os.getenv("NEO4J_PASSWORD")
)
```

## 📝 Common Use Cases

### 1. Daily Fragility Report

```python
import json
from datetime import datetime

# Run analysis
result = agent.analyze(metrics)

# Save report
filename = f"fragility_report_{datetime.now().strftime('%Y%m%d')}.json"
with open(filename, 'w') as f:
    json.dump(result, f, indent=2)

print(f"✓ Report saved: {filename}")
```

### 2. Alert on Critical Services

```python
critical_services = [
    s for s in result["fragility_scores"]
    if s["score"] >= 8.0
]

if critical_services:
    print("🚨 CRITICAL ALERT!")
    for service in critical_services:
        print(f"  {service['service']}: {service['score']}/10.0")
        # Send alert to monitoring system
        # send_alert(service)
```

### 3. Compare Over Time

```python
# Save current scores
current_scores = {
    s["service"]: s["score"]
    for s in result["fragility_scores"]
}

# Compare with previous
for service, score in current_scores.items():
    previous = previous_scores.get(service, 0)
    change = score - previous
    
    if change > 2.0:
        print(f"⚠️  {service}: +{change:.1f} (worsening)")
    elif change < -2.0:
        print(f"✓ {service}: {change:.1f} (improving)")
```

## 🐛 Troubleshooting

### "Failed to connect to Neo4j"

```bash
# Check Neo4j is running
cypher-shell -u neo4j -p password

# If not running, start it
neo4j start
```

### "No services found"

```bash
# Populate Neo4j first
cd ai-engine/agents/dependency_agent
python dependency_graph_manager.py
```

### "ModuleNotFoundError: No module named 'pydantic'"

```bash
# Install dependencies
cd ai-engine
pip install -r requirements.txt
```

## 📚 Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check [example_usage.py](example_usage.py) for more examples
- Review [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) for technical details

## 💡 Tips

1. **Run dependency agent first** to populate Neo4j
2. **Use environment variables** for credentials
3. **Filter by score** to focus on high-risk services
4. **Export to JSON** for integration with other tools
5. **Run tests** to verify everything works

## 🤝 Need Help?

- Check the [README.md](README.md) for detailed documentation
- Run tests to verify your setup: `python test_fragility_agent.py`
- Review example usage: `python example_usage.py`

---

**Made with Bob** 🤖