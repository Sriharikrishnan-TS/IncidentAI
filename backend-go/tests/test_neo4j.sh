#!/bin/bash

# Test script for Neo4j Integration
# This script tests the dependencies-extracted callback endpoint with sample data

echo "=== Neo4j Integration Test ==="
echo ""

# Configuration
BACKEND_URL="http://localhost:8080"
CALLBACK_API_KEY="d36c68357bc066ac159339826b3e75d0e4f7ab9be4e967b7e1ceed01db922784"

echo "1. Testing health endpoint..."
curl -s "$BACKEND_URL/health" | jq .
echo ""

echo "2. Testing dependencies-extracted callback with sample data..."
echo "   (This will store nodes and edges in Neo4j)"
echo ""

# Sample dependency graph data
curl -X POST "$BACKEND_URL/callback/dependencies-extracted" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $CALLBACK_API_KEY" \
  -d '{
    "repo_id": "test_repo_123",
    "dependencies": [
      {
        "source": "auth-service",
        "target": "database-service",
        "type": "DEPENDS_ON",
        "properties": {
          "weight": 1.0
        }
      },
      {
        "source": "checkout-service",
        "target": "auth-service",
        "type": "DEPENDS_ON",
        "properties": {
          "weight": 0.8
        }
      },
      {
        "source": "checkout-service",
        "target": "payment-service",
        "type": "DEPENDS_ON",
        "properties": {
          "weight": 0.9
        }
      },
      {
        "source": "payment-service",
        "target": "database-service",
        "type": "DEPENDS_ON",
        "properties": {
          "weight": 0.7
        }
      },
      {
        "source": "api-gateway",
        "target": "auth-service",
        "type": "CALLS",
        "properties": {
          "weight": 1.0
        }
      },
      {
        "source": "api-gateway",
        "target": "checkout-service",
        "type": "CALLS",
        "properties": {
          "weight": 0.9
        }
      }
    ]
  }' | jq .

echo ""
echo "3. Retrieving dependency graph from Neo4j..."
curl -s "$BACKEND_URL/dependency-graph/test_repo_123" | jq .

echo ""
echo "=== Test Complete ==="
echo ""
echo "Expected results:"
echo "  - Callback should return: status=success, nodes=6, edges=6"
echo "  - Dependency graph should show 6 nodes and 6 edges"
echo ""
echo "To run this test:"
echo "  1. Start Neo4j: docker run -p 7687:7687 -p 7474:7474 -e NEO4J_AUTH=neo4j/password neo4j:latest"
echo "  2. Start backend: CALLBACK_API_KEY=test-key-123 ./incidentos"
echo "  3. Run this script: bash test_neo4j.sh"

# Made with Bob
