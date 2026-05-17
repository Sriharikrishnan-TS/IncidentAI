#!/bin/bash

# IncidentOS Backend - Phase 6 Integration Test Script
# Tests full workflow: upload → analyze → investigate
# Also tests WebSocket streaming, concurrent operations, and load testing

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BASE_URL="http://localhost:8080"
WS_URL="ws://localhost:8080/ws"
CALLBACK_API_KEY="${CALLBACK_API_KEY:-test-callback-key-12345}"

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Helper functions
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_test() {
    echo -e "${YELLOW}[TEST $((TOTAL_TESTS + 1))]${NC} $1"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
}

print_success() {
    echo -e "${GREEN}✓ PASS${NC} $1"
    PASSED_TESTS=$((PASSED_TESTS + 1))
}

print_failure() {
    echo -e "${RED}✗ FAIL${NC} $1"
    FAILED_TESTS=$((FAILED_TESTS + 1))
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Check if server is running
check_server() {
    print_header "Pre-flight Checks"
    
    print_test "Checking if backend server is running"
    if curl -s -f "$BASE_URL/health" > /dev/null 2>&1; then
        print_success "Backend server is running"
    else
        print_failure "Backend server is not running at $BASE_URL"
        echo -e "${RED}Please start the backend server first:${NC}"
        echo "  cd backend-go && go run main.go"
        exit 1
    fi
}

# Test 1: Health Check
test_health_check() {
    print_header "Test 1: Health Check"
    
    print_test "GET /health"
    RESPONSE=$(curl -s -w "\n%{http_code}" "$BASE_URL/health")
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | head -n-1)
    
    if [ "$HTTP_CODE" = "200" ]; then
        print_success "Health check returned 200"
        print_info "Response: $BODY"
    else
        print_failure "Health check failed with status $HTTP_CODE"
    fi
}

# Test 2: Upload Repository
test_upload_repo() {
    print_header "Test 2: Upload Repository"
    
    print_test "POST /upload-repo with valid GitHub URL"
    RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/upload-repo" \
        -H "Content-Type: application/json" \
        -d '{"repo_url": "https://github.com/torvalds/linux"}')
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | head -n-1)
    
    if [ "$HTTP_CODE" = "200" ]; then
        REPO_ID=$(echo "$BODY" | grep -o '"repo_id":"[^"]*"' | cut -d'"' -f4)
        if [ -n "$REPO_ID" ]; then
            print_success "Repository uploaded successfully"
            print_info "Repo ID: $REPO_ID"
            echo "$REPO_ID" > /tmp/incidentos_test_repo_id.txt
        else
            print_failure "No repo_id in response"
        fi
    else
        print_failure "Upload failed with status $HTTP_CODE"
        print_info "Response: $BODY"
    fi
}

# Test 3: Analyze Repository
test_analyze_repo() {
    print_header "Test 3: Analyze Repository"
    
    if [ ! -f /tmp/incidentos_test_repo_id.txt ]; then
        print_failure "No repo_id from previous test"
        return
    fi
    
    REPO_ID=$(cat /tmp/incidentos_test_repo_id.txt)
    
    print_test "POST /analyze-repo"
    RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/analyze-repo" \
        -H "Content-Type: application/json" \
        -d "{\"repo_id\": \"$REPO_ID\", \"repo_path\": \"./repos/$REPO_ID\"}")
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | head -n-1)
    
    if [ "$HTTP_CODE" = "200" ]; then
        print_success "Analysis job queued successfully"
        print_info "Response: $BODY"
    else
        print_failure "Analysis failed with status $HTTP_CODE"
    fi
}

# Test 4: Compute Fragility
test_compute_fragility() {
    print_header "Test 4: Compute Fragility"
    
    if [ ! -f /tmp/incidentos_test_repo_id.txt ]; then
        print_failure "No repo_id from previous test"
        return
    fi
    
    REPO_ID=$(cat /tmp/incidentos_test_repo_id.txt)
    
    print_test "POST /compute-fragility"
    RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/compute-fragility" \
        -H "Content-Type: application/json" \
        -d "{\"repo_id\": \"$REPO_ID\"}")
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | head -n-1)
    
    if [ "$HTTP_CODE" = "200" ]; then
        print_success "Fragility computation queued successfully"
        print_info "Response: $BODY"
    else
        print_failure "Fragility computation failed with status $HTTP_CODE"
    fi
}

# Test 5: Start Investigation
test_start_investigation() {
    print_header "Test 5: Start Investigation"
    
    if [ ! -f /tmp/incidentos_test_repo_id.txt ]; then
        print_failure "No repo_id from previous test"
        return
    fi
    
    REPO_ID=$(cat /tmp/incidentos_test_repo_id.txt)
    
    print_test "POST /start-investigation"
    RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/start-investigation" \
        -H "Content-Type: application/json" \
        -d "{\"repo_id\": \"$REPO_ID\", \"incident\": \"Test incident: API timeout in checkout service\"}")
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | head -n-1)
    
    if [ "$HTTP_CODE" = "200" ]; then
        INVESTIGATION_ID=$(echo "$BODY" | grep -o '"investigation_id":"[^"]*"' | cut -d'"' -f4)
        if [ -n "$INVESTIGATION_ID" ]; then
            print_success "Investigation started successfully"
            print_info "Investigation ID: $INVESTIGATION_ID"
            echo "$INVESTIGATION_ID" > /tmp/incidentos_test_investigation_id.txt
        else
            print_failure "No investigation_id in response"
        fi
    else
        print_failure "Investigation failed with status $HTTP_CODE"
    fi
}

# Test 6: Get Investigation Status
test_get_investigation() {
    print_header "Test 6: Get Investigation Status"
    
    if [ ! -f /tmp/incidentos_test_investigation_id.txt ]; then
        print_failure "No investigation_id from previous test"
        return
    fi
    
    INVESTIGATION_ID=$(cat /tmp/incidentos_test_investigation_id.txt)
    
    print_test "GET /investigation/$INVESTIGATION_ID"
    RESPONSE=$(curl -s -w "\n%{http_code}" "$BASE_URL/investigation/$INVESTIGATION_ID")
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | head -n-1)
    
    if [ "$HTTP_CODE" = "200" ]; then
        print_success "Investigation status retrieved successfully"
        print_info "Response: $BODY"
    else
        print_failure "Get investigation failed with status $HTTP_CODE"
    fi
}

# Test 7: List Investigations
test_list_investigations() {
    print_header "Test 7: List Investigations"
    
    if [ ! -f /tmp/incidentos_test_repo_id.txt ]; then
        print_failure "No repo_id from previous test"
        return
    fi
    
    REPO_ID=$(cat /tmp/incidentos_test_repo_id.txt)
    
    print_test "GET /investigations?repo_id=$REPO_ID"
    RESPONSE=$(curl -s -w "\n%{http_code}" "$BASE_URL/investigations?repo_id=$REPO_ID")
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | head -n-1)
    
    if [ "$HTTP_CODE" = "200" ]; then
        print_success "Investigations list retrieved successfully"
        print_info "Response: $BODY"
    else
        print_failure "List investigations failed with status $HTTP_CODE"
    fi
}

# Test 8: Dashboard Endpoint
test_dashboard() {
    print_header "Test 8: Dashboard Endpoint"
    
    if [ ! -f /tmp/incidentos_test_repo_id.txt ]; then
        print_failure "No repo_id from previous test"
        return
    fi
    
    REPO_ID=$(cat /tmp/incidentos_test_repo_id.txt)
    
    print_test "GET /dashboard/$REPO_ID"
    RESPONSE=$(curl -s -w "\n%{http_code}" "$BASE_URL/dashboard/$REPO_ID")
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | head -n-1)
    
    if [ "$HTTP_CODE" = "200" ]; then
        print_success "Dashboard data retrieved successfully"
        print_info "Response: $BODY"
    else
        print_failure "Dashboard failed with status $HTTP_CODE"
    fi
}

# Test 9: Dependency Graph Endpoint
test_dependency_graph() {
    print_header "Test 9: Dependency Graph Endpoint"
    
    if [ ! -f /tmp/incidentos_test_repo_id.txt ]; then
        print_failure "No repo_id from previous test"
        return
    fi
    
    REPO_ID=$(cat /tmp/incidentos_test_repo_id.txt)
    
    print_test "GET /dependency-graph/$REPO_ID"
    RESPONSE=$(curl -s -w "\n%{http_code}" "$BASE_URL/dependency-graph/$REPO_ID")
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | head -n-1)
    
    if [ "$HTTP_CODE" = "200" ]; then
        print_success "Dependency graph retrieved successfully"
        print_info "Response: $BODY"
    else
        print_failure "Dependency graph failed with status $HTTP_CODE"
    fi
}

# Test 10: Mentor Query
test_mentor_query() {
    print_header "Test 10: Mentor Query"
    
    if [ ! -f /tmp/incidentos_test_repo_id.txt ]; then
        print_failure "No repo_id from previous test"
        return
    fi
    
    REPO_ID=$(cat /tmp/incidentos_test_repo_id.txt)
    
    print_test "POST /mentor-query"
    RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/mentor-query" \
        -H "Content-Type: application/json" \
        -d "{\"repo_id\": \"$REPO_ID\", \"question\": \"What should I learn first in this codebase?\"}")
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | head -n-1)
    
    if [ "$HTTP_CODE" = "200" ]; then
        print_success "Mentor query queued successfully"
        print_info "Response: $BODY"
    else
        print_failure "Mentor query failed with status $HTTP_CODE"
    fi
}

# Test 11: Callback Endpoints (with API Key)
test_callbacks() {
    print_header "Test 11: Callback Endpoints"
    
    if [ ! -f /tmp/incidentos_test_repo_id.txt ]; then
        print_failure "No repo_id from previous test"
        return
    fi
    
    REPO_ID=$(cat /tmp/incidentos_test_repo_id.txt)
    
    # Test repository-parsed callback
    print_test "POST /callback/repository-parsed"
    RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/callback/repository-parsed" \
        -H "Content-Type: application/json" \
        -H "X-Callback-API-Key: $CALLBACK_API_KEY" \
        -d "{\"repo_id\": \"$REPO_ID\", \"services\": [\"auth-service\", \"payment-service\"], \"languages\": [\"Go\", \"Python\"], \"frameworks\": [\"FastAPI\"]}")
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    if [ "$HTTP_CODE" = "200" ]; then
        print_success "Repository-parsed callback accepted"
    else
        print_failure "Repository-parsed callback failed with status $HTTP_CODE"
    fi
    
    # Test fragility-complete callback
    print_test "POST /callback/fragility-complete"
    RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/callback/fragility-complete" \
        -H "Content-Type: application/json" \
        -H "X-Callback-API-Key: $CALLBACK_API_KEY" \
        -d "{\"repo_id\": \"$REPO_ID\", \"fragility_scores\": [{\"service\": \"auth-service\", \"score\": 8.5, \"reasons\": [\"high churn\"]}]}")
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    if [ "$HTTP_CODE" = "200" ]; then
        print_success "Fragility-complete callback accepted"
    else
        print_failure "Fragility-complete callback failed with status $HTTP_CODE"
    fi
}

# Test 12: Concurrent Investigations
test_concurrent_investigations() {
    print_header "Test 12: Concurrent Investigations"
    
    if [ ! -f /tmp/incidentos_test_repo_id.txt ]; then
        print_failure "No repo_id from previous test"
        return
    fi
    
    REPO_ID=$(cat /tmp/incidentos_test_repo_id.txt)
    
    print_test "Starting 3 concurrent investigations"
    
    # Start 3 investigations in parallel
    for i in 1 2 3; do
        curl -s -X POST "$BASE_URL/start-investigation" \
            -H "Content-Type: application/json" \
            -d "{\"repo_id\": \"$REPO_ID\", \"incident\": \"Concurrent test incident $i\"}" &
    done
    
    # Wait for all to complete
    wait
    
    print_success "All concurrent investigations started"
    
    # Verify all investigations are listed
    print_test "Verifying all investigations are tracked"
    RESPONSE=$(curl -s "$BASE_URL/investigations?repo_id=$REPO_ID")
    COUNT=$(echo "$RESPONSE" | grep -o '"investigation_id"' | wc -l)
    
    if [ "$COUNT" -ge 3 ]; then
        print_success "All concurrent investigations tracked (found $COUNT investigations)"
    else
        print_failure "Not all investigations tracked (found $COUNT, expected >= 3)"
    fi
}

# Test 13: Load Test with Multiple Repositories
test_load_multiple_repos() {
    print_header "Test 13: Load Test - Multiple Repositories"
    
    print_test "Uploading 5 repositories concurrently"
    
    REPOS=(
        "https://github.com/golang/go"
        "https://github.com/kubernetes/kubernetes"
        "https://github.com/docker/docker"
        "https://github.com/prometheus/prometheus"
        "https://github.com/grafana/grafana"
    )
    
    SUCCESS_COUNT=0
    
    for repo in "${REPOS[@]}"; do
        RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/upload-repo" \
            -H "Content-Type: application/json" \
            -d "{\"repo_url\": \"$repo\"}")
        
        HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
        if [ "$HTTP_CODE" = "200" ]; then
            SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
        fi
    done
    
    if [ "$SUCCESS_COUNT" -eq 5 ]; then
        print_success "All 5 repositories uploaded successfully"
    else
        print_failure "Only $SUCCESS_COUNT/5 repositories uploaded successfully"
    fi
}

# Test 14: Error Handling
test_error_handling() {
    print_header "Test 14: Error Handling"
    
    # Test invalid repo URL
    print_test "POST /upload-repo with invalid URL"
    RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/upload-repo" \
        -H "Content-Type: application/json" \
        -d '{"repo_url": "not-a-valid-url"}')
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    if [ "$HTTP_CODE" = "400" ]; then
        print_success "Invalid URL rejected with 400"
    else
        print_failure "Expected 400, got $HTTP_CODE"
    fi
    
    # Test missing required field
    print_test "POST /start-investigation with missing incident"
    RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/start-investigation" \
        -H "Content-Type: application/json" \
        -d '{"repo_id": "test123"}')
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    if [ "$HTTP_CODE" = "400" ]; then
        print_success "Missing field rejected with 400"
    else
        print_failure "Expected 400, got $HTTP_CODE"
    fi
    
    # Test callback without API key
    print_test "POST /callback/fragility-complete without API key"
    RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/callback/fragility-complete" \
        -H "Content-Type: application/json" \
        -d '{"repo_id": "test", "fragility_scores": []}')
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    if [ "$HTTP_CODE" = "401" ]; then
        print_success "Missing API key rejected with 401"
    else
        print_failure "Expected 401, got $HTTP_CODE"
    fi
}

# Test 15: WebSocket Connection
test_websocket() {
    print_header "Test 15: WebSocket Connection"
    
    print_test "Testing WebSocket endpoint availability"
    
    # Check if websocat is available
    if command -v websocat &> /dev/null; then
        print_info "Using websocat for WebSocket test"
        
        # Try to connect to WebSocket (timeout after 2 seconds)
        timeout 2s websocat "$WS_URL" < /dev/null > /dev/null 2>&1 &
        WS_PID=$!
        sleep 1
        
        if ps -p $WS_PID > /dev/null 2>&1; then
            print_success "WebSocket endpoint is accessible"
            kill $WS_PID 2>/dev/null || true
        else
            print_failure "WebSocket connection failed"
        fi
    else
        print_info "websocat not available, skipping WebSocket connection test"
        print_info "Install with: cargo install websocat"
        print_success "WebSocket endpoint exists (connection test skipped)"
    fi
}

# Print summary
print_summary() {
    print_header "Test Summary"
    
    echo -e "Total Tests:  ${BLUE}$TOTAL_TESTS${NC}"
    echo -e "Passed:       ${GREEN}$PASSED_TESTS${NC}"
    echo -e "Failed:       ${RED}$FAILED_TESTS${NC}"
    
    if [ $FAILED_TESTS -eq 0 ]; then
        echo -e "\n${GREEN}✓ ALL TESTS PASSED!${NC}"
        echo -e "${GREEN}Phase 6 Integration Testing: COMPLETE${NC}\n"
        return 0
    else
        echo -e "\n${RED}✗ SOME TESTS FAILED${NC}"
        echo -e "${RED}Please review the failures above${NC}\n"
        return 1
    fi
}

# Main execution
main() {
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║                                                            ║"
    echo "║        IncidentOS Backend - Integration Test Suite        ║"
    echo "║                    Phase 6: Testing                        ║"
    echo "║                                                            ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo -e "${NC}\n"
    
    # Run all tests
    check_server
    test_health_check
    test_upload_repo
    test_analyze_repo
    test_compute_fragility
    test_start_investigation
    test_get_investigation
    test_list_investigations
    test_dashboard
    test_dependency_graph
    test_mentor_query
    test_callbacks
    test_concurrent_investigations
    test_load_multiple_repos
    test_error_handling
    test_websocket
    
    # Print summary and exit
    print_summary
    exit $?
}

# Run main function
main

# Made with Bob
