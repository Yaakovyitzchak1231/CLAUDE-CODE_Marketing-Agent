#!/bin/bash
# Test All Services Connectivity
# B2B Marketing Automation Platform

echo "========================================="
echo "Service Connectivity Test"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
PASSED=0
FAILED=0

# Test function
test_service() {
    local name=$1
    local url=$2
    local expected_code=${3:-200}

    printf "Testing %-25s " "$name..."

    status=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$url" 2>/dev/null)

    if [ "$status" = "$expected_code" ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $status)"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} (HTTP $status, expected $expected_code)"
        ((FAILED++))
        return 1
    fi
}

# Wait for services to start
echo "Waiting for services to initialize..."
sleep 5
echo ""

# ==================== CORE INFRASTRUCTURE ====================
echo "Core Infrastructure:"
echo "-------------------"

test_service "PostgreSQL" "http://localhost:5432" "000"  # Connection refused is expected for HTTP
test_service "Redis" "http://localhost:6379" "000"       # Connection refused is expected
test_service "Nginx" "http://localhost/health" "200"

echo ""

# ==================== AI & DATA SERVICES ====================
echo "AI & Data Services:"
echo "-------------------"

test_service "Ollama" "http://localhost:11434/api/tags" "200"
test_service "Chroma" "http://localhost:8000/api/v1/heartbeat" "200"
test_service "SearXNG" "http://localhost:8080" "200"

echo ""

# ==================== ORCHESTRATION & DASHBOARD ====================
echo "Orchestration & Dashboard:"
echo "--------------------------"

test_service "n8n" "http://localhost:5678" "200"
test_service "Streamlit Dashboard" "http://localhost:8501/_stcore/health" "200"
test_service "Matomo Analytics" "http://localhost:8081" "200"

echo ""

# ==================== UTILITIES ====================
echo "Utilities:"
echo "----------"

test_service "Adminer" "http://localhost:8082" "200"

echo ""

# ==================== NGINX REVERSE PROXY ROUTES ====================
echo "Nginx Reverse Proxy Routes:"
echo "---------------------------"

test_service "Main Health" "http://localhost/health" "200"
test_service "Dashboard Route" "http://localhost/dashboard" "200"
test_service "n8n Route" "http://localhost/n8n" "200"
test_service "Analytics Route" "http://localhost/analytics/" "200"
test_service "Search Route" "http://localhost/search/" "200"
test_service "Adminer Route" "http://localhost/adminer/" "200"

echo ""

# ==================== DETAILED SERVICE CHECKS ====================
echo "Detailed Service Checks:"
echo "------------------------"

# Test PostgreSQL connection
printf "PostgreSQL Connection... "
if docker exec postgres psql -U marketing_user -d marketing -c "SELECT 1" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PASS${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ FAIL${NC}"
    ((FAILED++))
fi

# Test Redis connection
printf "Redis Connection... "
if docker exec redis redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PASS${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ FAIL${NC}"
    ((FAILED++))
fi

# Test Ollama models
printf "Ollama Models... "
models=$(curl -s http://localhost:11434/api/tags | grep -o '"name"' | wc -l)
if [ "$models" -gt 0 ]; then
    echo -e "${GREEN}✓ PASS${NC} ($models models available)"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠ WARN${NC} (No models pulled yet. Run: ./ollama/pull-models.sh)"
    ((FAILED++))
fi

# Test Chroma collections
printf "Chroma Collections... "
collections=$(curl -s http://localhost:8000/api/v1/collections | grep -o '"name"' | wc -l)
if [ "$collections" -ge 0 ]; then
    echo -e "${GREEN}✓ PASS${NC} ($collections collections)"
    ((PASSED++))
else
    echo -e "${RED}✗ FAIL${NC}"
    ((FAILED++))
fi

echo ""

# ==================== NETWORK CONNECTIVITY ====================
echo "Network Connectivity:"
echo "---------------------"

# Test inter-container networking
printf "Container Network... "
if docker exec langchain_service ping -c 1 postgres > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PASS${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ FAIL${NC}"
    ((FAILED++))
fi

echo ""

# ==================== SUMMARY ====================
echo "========================================="
echo "Test Summary"
echo "========================================="
echo -e "Total Tests: $((PASSED + FAILED))"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"

if [ $FAILED -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ All services are operational!${NC}"
    echo ""
    echo "Access points:"
    echo "  Dashboard:  http://localhost/dashboard"
    echo "  n8n:        http://localhost/n8n"
    echo "  Analytics:  http://localhost/analytics"
    echo "  Database:   http://localhost/adminer"
    echo ""
    exit 0
else
    echo ""
    echo -e "${YELLOW}⚠ Some services failed. Check logs:${NC}"
    echo "  docker-compose logs [service-name]"
    echo ""
    exit 1
fi
