#!/bin/bash

# Test script for Phase 5 callback endpoints
# Tests all new callback endpoints with mock AI Engine responses

set -e

BASE_URL="http://localhost:8080"
API_KEY="test-callback-key-123"

echo "=========================================="
echo "Testing Phase 5 Callback Endpoints"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Function to test an endpoint
test_endpoint() {
    local name=$1
    local endpoint=$2
    local data=$3
    
    echo -e "${YELLOW}Testing: $name${NC}"
    echo "Endpoint: POST $endpoint"
    
    response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL$endpoint" \
        -H "Content-Type: application/json" \
        -H "X-API-Key: $API_KEY" \
        -d "$data")
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [ "$http_code" = "200" ]; then
        echo -e "${GREEN}✓ PASSED${NC} (HTTP $http_code)"
        echo "Response: $body"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗ FAILED${NC} (HTTP $http_code)"
        echo "Response: $body"
        ((TESTS_FAILED++))
    fi
    echo ""
}

echo "Note: Make sure the backend is running with:"
echo "  CALLBACK_API_KEY=test-callback-key-123 ./incidentos"
echo ""
sleep 2

# Test 1: Repository Parsed Callback
test_endpoint \
    "Repository Parsed Callback" \
    "/callback/repository-parsed" \
    '{
        "repo_id": "test_repo_123",
        "services": ["auth-service", "payment-service", "checkout-service"],
        "languages": ["Python", "TypeScript", "Go"],
        "frameworks": ["FastAPI", "Next.js", "Gin"]
    }'

# Test 2: Git History Analyzed Callback
test_endpoint \
    "Git History Analyzed Callback" \
    "/callback/git-history-analyzed" \
    '{
        "repo_id": "test_repo_123",
        "high_churn_services": ["auth-service", "payment-service"],
        "recent_commits": 245,
        "top_contributors": ["dev1", "dev2", "dev3"]
    }'

# Test 3: Fragility Complete Callback
test_endpoint \
    "Fragility Complete Callback" \
    "/callback/fragility-complete" \
    '{
        "repo_id": "test_repo_123",
        "fragility_scores": [
            {
                "service": "auth-service",
                "score": 8.7,
                "reasons": ["high commit churn", "high dependency centrality", "recent regressions"]
            },
            {
                "service": "payment-service",
                "score": 7.2,
                "reasons": ["moderate churn", "critical path"]
            },
            {
                "service": "checkout-service",
                "score": 4.3,
                "reasons": ["moderate churn"]
            }
        ]
    }'

# Test 4: Mentor Response Callback
test_endpoint \
    "Mentor Response Callback" \
    "/callback/mentor-response" \
    '{
        "repo_id": "test_repo_123",
        "question": "What should I learn first?",
        "answer": "Start with auth-service because it is central to the architecture and is depended on by multiple services. It handles authentication and authorization for the entire system."
    }'

# Test 5: Test Dashboard with Real Data
echo -e "${YELLOW}Testing: Dashboard with Real Data${NC}"
echo "Endpoint: GET /dashboard/test_repo_123"

dashboard_response=$(curl -s -w "\n%{http_code}" "$BASE_URL/dashboard/test_repo_123")
dashboard_http_code=$(echo "$dashboard_response" | tail -n1)
dashboard_body=$(echo "$dashboard_response" | head -n-1)

if [ "$dashboard_http_code" = "200" ]; then
    echo -e "${GREEN}✓ PASSED${NC} (HTTP $dashboard_http_code)"
    echo "Response: $dashboard_body"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ FAILED${NC} (HTTP $dashboard_http_code)"
    echo "Response: $dashboard_body"
    ((TESTS_FAILED++))
fi
echo ""

# Test 6: Test without API Key (should fail)
echo -e "${YELLOW}Testing: Callback without API Key (should fail)${NC}"
echo "Endpoint: POST /callback/fragility-complete"

no_key_response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/callback/fragility-complete" \
    -H "Content-Type: application/json" \
    -d '{"repo_id": "test_repo_123", "fragility_scores": []}')

no_key_http_code=$(echo "$no_key_response" | tail -n1)
no_key_body=$(echo "$no_key_response" | head -n-1)

if [ "$no_key_http_code" = "401" ]; then
    echo -e "${GREEN}✓ PASSED${NC} (HTTP $no_key_http_code - Correctly rejected)"
    echo "Response: $no_key_body"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ FAILED${NC} (HTTP $no_key_http_code - Should be 401)"
    echo "Response: $no_key_body"
    ((TESTS_FAILED++))
fi
echo ""

# Test 7: Test with wrong API Key (should fail)
echo -e "${YELLOW}Testing: Callback with wrong API Key (should fail)${NC}"
echo "Endpoint: POST /callback/fragility-complete"

wrong_key_response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/callback/fragility-complete" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: wrong-key" \
    -d '{"repo_id": "test_repo_123", "fragility_scores": []}')

wrong_key_http_code=$(echo "$wrong_key_response" | tail -n1)
wrong_key_body=$(echo "$wrong_key_response" | head -n-1)

if [ "$wrong_key_http_code" = "401" ]; then
    echo -e "${GREEN}✓ PASSED${NC} (HTTP $wrong_key_http_code - Correctly rejected)"
    echo "Response: $wrong_key_body"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ FAILED${NC} (HTTP $wrong_key_http_code - Should be 401)"
    echo "Response: $wrong_key_body"
    ((TESTS_FAILED++))
fi
echo ""

# Summary
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"
echo "Total Tests: $((TESTS_PASSED + TESTS_FAILED))"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed! ✓${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed! ✗${NC}"
    exit 1
fi

# Made with Bob
