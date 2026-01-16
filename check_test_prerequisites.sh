#!/bin/bash
# Pre-flight check for Brand Voice E2E tests
# Verifies all services and dependencies are ready

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Brand Voice E2E Test - Pre-flight Check${NC}"
echo "========================================"
echo ""

SUCCESS_COUNT=0
FAIL_COUNT=0

check_pass() {
    echo -e "${GREEN}✓ $1${NC}"
    SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
}

check_fail() {
    echo -e "${RED}✗ $1${NC}"
    FAIL_COUNT=$((FAIL_COUNT + 1))
}

check_warn() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Check 1: curl available
echo "Checking dependencies..."
if command -v curl &> /dev/null; then
    check_pass "curl is installed"
else
    check_fail "curl is not installed"
fi

# Check 2: Python available (optional)
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1)
    check_pass "Python is installed: $PYTHON_VERSION"

    # Check for requests library
    if python3 -c "import requests" 2>/dev/null; then
        check_pass "Python requests library is installed"
    else
        check_warn "Python requests library not found (pip install requests)"
    fi
else
    check_warn "Python 3 not found (optional, bash tests will still work)"
fi

echo ""
echo "Checking services..."

# Check 3: PostgreSQL
if curl -s http://localhost:5432 &> /dev/null; then
    check_pass "PostgreSQL port 5432 is accessible"
else
    check_warn "PostgreSQL might not be running (some tests may fail)"
fi

# Check 4: LangChain Service
echo -n "Checking LangChain service health... "
if HEALTH_RESPONSE=$(curl -s http://localhost:8001/health 2>/dev/null); then
    if [ -n "$HEALTH_RESPONSE" ]; then
        check_pass "LangChain service is running at http://localhost:8001"
    else
        check_fail "LangChain service responded but returned empty response"
    fi
else
    check_fail "LangChain service is not accessible at http://localhost:8001"
fi

# Check 5: API endpoints available
echo -n "Checking brand voice API endpoints... "
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/docs | grep -q "200"; then
    check_pass "OpenAPI docs accessible"

    # Try to fetch profiles (should return empty array or data)
    PROFILES_RESPONSE=$(curl -s http://localhost:8001/brand-voice/profiles)
    if echo "$PROFILES_RESPONSE" | grep -q '\[' || echo "$PROFILES_RESPONSE" | grep -q "detail"; then
        check_pass "Brand voice endpoints responding"
    else
        check_fail "Brand voice endpoints not responding correctly"
    fi
else
    check_fail "API documentation not accessible"
fi

# Check 6: Streamlit (optional)
echo -n "Checking Streamlit dashboard... "
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8501 | grep -q "200"; then
    check_pass "Streamlit dashboard accessible at http://localhost:8501 (optional)"
else
    check_warn "Streamlit dashboard not accessible (optional for automated tests)"
fi

echo ""
echo "Checking database schema..."

# Check 7: Database tables (if docker is available)
if command -v docker &> /dev/null; then
    # Try to check if brand_voice_profiles table exists
    TABLE_CHECK=$(docker compose exec -T postgres psql -U marketing_user -d marketing -t -c "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'brand_voice_profiles');" 2>/dev/null || echo "false")

    if echo "$TABLE_CHECK" | grep -q "t"; then
        check_pass "brand_voice_profiles table exists"
    else
        check_fail "brand_voice_profiles table not found"
    fi

    # Check campaigns table has brand_voice_profile_id column
    COLUMN_CHECK=$(docker compose exec -T postgres psql -U marketing_user -d marketing -t -c "SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'campaigns' AND column_name = 'brand_voice_profile_id');" 2>/dev/null || echo "false")

    if echo "$COLUMN_CHECK" | grep -q "t"; then
        check_pass "campaigns.brand_voice_profile_id column exists"
    else
        check_fail "campaigns.brand_voice_profile_id column not found"
    fi
else
    check_warn "Docker not available, skipping database checks"
fi

echo ""
echo "========================================"
echo -e "Results: ${GREEN}$SUCCESS_COUNT passed${NC}, ${RED}$FAIL_COUNT failed${NC}"
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed! Ready to run E2E tests.${NC}"
    echo ""
    echo "Run tests with:"
    echo "  python3 test_brand_voice_e2e.py  (recommended)"
    echo "  ./test_brand_voice_e2e.sh        (alternative)"
    echo ""
    exit 0
else
    echo -e "${RED}✗ Some checks failed. Please fix issues before running tests.${NC}"
    echo ""
    echo "To start services:"
    echo "  cd /c/Users/jacob/marketing-agent"
    echo "  docker compose up -d postgres langchain-service"
    echo ""
    exit 1
fi
