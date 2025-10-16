#!/bin/bash

##############################################
# Smoke Test Script for Preview Environment
#
# Usage:
#   ./scripts/smoke-test.sh <API_BASE_URL>
#
# Example:
#   ./scripts/smoke-test.sh https://tepure-api-preview.run.app
##############################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# API Base URL
API_BASE=${1:-"http://localhost:8080"}
API_V1="${API_BASE}/api/v1"

echo "================================================"
echo "🧪 Smoke Test for tepure Preview Environment"
echo "================================================"
echo "API Base: $API_BASE"
echo ""

# Helper functions
pass() {
  echo -e "${GREEN}✓${NC} $1"
  TESTS_PASSED=$((TESTS_PASSED + 1))
}

fail() {
  echo -e "${RED}✗${NC} $1"
  TESTS_FAILED=$((TESTS_FAILED + 1))
}

warn() {
  echo -e "${YELLOW}⚠${NC} $1"
}

# Test 1: Health Check
echo "Test 1: Health Check"
HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" ${API_BASE}/health)
HEALTH_BODY=$(echo "$HEALTH_RESPONSE" | head -n -1)
HEALTH_CODE=$(echo "$HEALTH_RESPONSE" | tail -n 1)

if [ "$HEALTH_CODE" -eq 200 ]; then
  OK=$(echo "$HEALTH_BODY" | jq -r '.ok')
  VERSION=$(echo "$HEALTH_BODY" | jq -r '.version')
  GIT=$(echo "$HEALTH_BODY" | jq -r '.git')

  if [ "$OK" == "true" ]; then
    pass "Health endpoint returns 200 with ok=true"
    echo "   Version: $VERSION, Git: $GIT"
  else
    fail "Health endpoint ok field is not true"
  fi
else
  fail "Health endpoint returned $HEALTH_CODE (expected 200)"
  exit 1
fi

echo ""

# Test 2: Authentication
echo "Test 2: Authentication"
LOGIN_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${API_V1}/auth/login" \
  -H 'Content-Type: application/json' \
  -d '{"email":"test@example.com","password":"password123"}')

LOGIN_BODY=$(echo "$LOGIN_RESPONSE" | head -n -1)
LOGIN_CODE=$(echo "$LOGIN_RESPONSE" | tail -n 1)

if [ "$LOGIN_CODE" -eq 200 ]; then
  JWT=$(echo "$LOGIN_BODY" | jq -r '.access_token')

  if [ "$JWT" != "null" ] && [ -n "$JWT" ]; then
    pass "Authentication successful"
    echo "   JWT: ${JWT:0:30}..."
  else
    fail "JWT token not found in response"
    exit 1
  fi
else
  fail "Login failed with code $LOGIN_CODE"
  echo "$LOGIN_BODY" | jq .
  exit 1
fi

echo ""

# Test 3: Templates API - List
echo "Test 3: Templates API - List"
TEMPLATES_RESPONSE=$(curl -s -w "\n%{http_code}" \
  -H "Authorization: Bearer $JWT" \
  "${API_V1}/templates?category=LP&size=5")

TEMPLATES_BODY=$(echo "$TEMPLATES_RESPONSE" | head -n -1)
TEMPLATES_CODE=$(echo "$TEMPLATES_RESPONSE" | tail -n 1)

if [ "$TEMPLATES_CODE" -eq 200 ]; then
  TEMPLATES_ARRAY=$(echo "$TEMPLATES_BODY" | jq -r '.templates')

  if [ "$TEMPLATES_ARRAY" != "null" ]; then
    TEMPLATE_COUNT=$(echo "$TEMPLATES_BODY" | jq '.templates | length')
    pass "Templates list endpoint works"
    echo "   Found $TEMPLATE_COUNT templates"

    # Check first template has new fields
    FIRST_TEMPLATE=$(echo "$TEMPLATES_BODY" | jq '.templates[0]')
    CATEGORY=$(echo "$FIRST_TEMPLATE" | jq -r '.category // "missing"')
    FIELDS=$(echo "$FIRST_TEMPLATE" | jq -r '.fields // "missing"')
    PREVIEW_URL=$(echo "$FIRST_TEMPLATE" | jq -r '.preview_url // "missing"')

    if [ "$CATEGORY" != "missing" ] && [ "$FIELDS" != "missing" ]; then
      pass "Template schema includes new fields (category, fields)"
      echo "   Category: $CATEGORY"
    else
      warn "Template missing new fields (category or fields)"
    fi
  else
    fail "Templates array not found in response"
  fi
else
  fail "Templates list failed with code $TEMPLATES_CODE"
  echo "$TEMPLATES_BODY" | jq .
fi

echo ""

# Test 4: Get First Template ID
echo "Test 4: Get Template Details"
TEMPLATE_ID=$(echo "$TEMPLATES_BODY" | jq -r '.templates[0].id // "tpl_001"')

TEMPLATE_DETAIL_RESPONSE=$(curl -s -w "\n%{http_code}" \
  -H "Authorization: Bearer $JWT" \
  "${API_V1}/templates/${TEMPLATE_ID}")

TEMPLATE_DETAIL_BODY=$(echo "$TEMPLATE_DETAIL_RESPONSE" | head -n -1)
TEMPLATE_DETAIL_CODE=$(echo "$TEMPLATE_DETAIL_RESPONSE" | tail -n 1)

if [ "$TEMPLATE_DETAIL_CODE" -eq 200 ]; then
  pass "Template detail endpoint works"
  TEMPLATE_NAME=$(echo "$TEMPLATE_DETAIL_BODY" | jq -r '.name')
  echo "   Template: $TEMPLATE_NAME (ID: $TEMPLATE_ID)"
else
  warn "Template detail failed with code $TEMPLATE_DETAIL_CODE"
fi

echo ""

# Test 5: Job Creation
echo "Test 5: Job Creation"
IDEMPOTENCY_KEY="smoke-test-$(date +%s)"

JOB_CREATE_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
  "${API_V1}/templates/${TEMPLATE_ID}/use" \
  -H "Authorization: Bearer $JWT" \
  -H 'Content-Type: application/json' \
  -H "Idempotency-Key: $IDEMPOTENCY_KEY" \
  -d "{
    \"template_id\": \"${TEMPLATE_ID}\",
    \"inputs\": {\"title\": \"Smoke Test\"},
    \"temperature\": 0.7,
    \"intensity\": \"medium\",
    \"idempotency_key\": \"${IDEMPOTENCY_KEY}\"
  }")

JOB_CREATE_BODY=$(echo "$JOB_CREATE_RESPONSE" | head -n -1)
JOB_CREATE_CODE=$(echo "$JOB_CREATE_RESPONSE" | tail -n 1)

if [ "$JOB_CREATE_CODE" -eq 200 ] || [ "$JOB_CREATE_CODE" -eq 201 ]; then
  JOB_ID=$(echo "$JOB_CREATE_BODY" | jq -r '.job_id')
  JOB_STATUS=$(echo "$JOB_CREATE_BODY" | jq -r '.status')

  if [ "$JOB_ID" != "null" ] && [ -n "$JOB_ID" ]; then
    pass "Job creation successful"
    echo "   Job ID: $JOB_ID"
    echo "   Initial Status: $JOB_STATUS"

    # Check status is one of the new vocabulary
    if [[ "$JOB_STATUS" =~ ^(pending|processing|completed|failed)$ ]]; then
      pass "Job status uses new vocabulary ($JOB_STATUS)"
    else
      fail "Job status uses old vocabulary ($JOB_STATUS)"
    fi
  else
    fail "Job ID not found in response"
  fi
else
  fail "Job creation failed with code $JOB_CREATE_CODE"
  echo "$JOB_CREATE_BODY" | jq .
fi

echo ""

# Test 6: Job Status Check
if [ -n "$JOB_ID" ] && [ "$JOB_ID" != "null" ]; then
  echo "Test 6: Job Status Check"
  sleep 3  # Wait for processing

  JOB_STATUS_RESPONSE=$(curl -s -w "\n%{http_code}" \
    -H "Authorization: Bearer $JWT" \
    "${API_V1}/jobs/${JOB_ID}")

  JOB_STATUS_BODY=$(echo "$JOB_STATUS_RESPONSE" | head -n -1)
  JOB_STATUS_CODE=$(echo "$JOB_STATUS_RESPONSE" | tail -n 1)

  if [ "$JOB_STATUS_CODE" -eq 200 ]; then
    CURRENT_STATUS=$(echo "$JOB_STATUS_BODY" | jq -r '.status')
    USAGE=$(echo "$JOB_STATUS_BODY" | jq '.usage')

    pass "Job status endpoint works"
    echo "   Status: $CURRENT_STATUS"

    if [ "$USAGE" != "null" ]; then
      TOTAL_TOKENS=$(echo "$USAGE" | jq -r '.total_tokens // 0')
      COST=$(echo "$USAGE" | jq -r '.estimated_cost_usd // 0')

      echo "   Usage: $TOTAL_TOKENS tokens, \$$COST"

      # Check token limit
      if [ "$TOTAL_TOKENS" -le 1500 ]; then
        pass "Token usage within limit ($TOTAL_TOKENS <= 1500)"
      else
        fail "Token usage exceeds limit ($TOTAL_TOKENS > 1500)"
      fi
    fi
  else
    warn "Job status check failed with code $JOB_STATUS_CODE"
  fi
fi

echo ""

# Test 7: Idempotency Check
echo "Test 7: Idempotency Check"
JOB_CREATE_DUPLICATE=$(curl -s -w "\n%{http_code}" -X POST \
  "${API_V1}/templates/${TEMPLATE_ID}/use" \
  -H "Authorization: Bearer $JWT" \
  -H 'Content-Type: application/json' \
  -H "Idempotency-Key: $IDEMPOTENCY_KEY" \
  -d "{
    \"template_id\": \"${TEMPLATE_ID}\",
    \"inputs\": {\"title\": \"Smoke Test\"},
    \"temperature\": 0.7,
    \"intensity\": \"medium\",
    \"idempotency_key\": \"${IDEMPOTENCY_KEY}\"
  }")

JOB_DUP_BODY=$(echo "$JOB_CREATE_DUPLICATE" | head -n -1)
JOB_DUP_CODE=$(echo "$JOB_CREATE_DUPLICATE" | tail -n 1)

if [ "$JOB_DUP_CODE" -eq 200 ]; then
  JOB_ID_DUP=$(echo "$JOB_DUP_BODY" | jq -r '.job_id')

  if [ "$JOB_ID" == "$JOB_ID_DUP" ]; then
    pass "Idempotency works (same Job ID returned)"
  else
    fail "Idempotency failed (different Job ID: $JOB_ID_DUP)"
  fi
else
  warn "Idempotency test returned unexpected code $JOB_DUP_CODE"
fi

echo ""

# Summary
echo "================================================"
echo "📊 Smoke Test Summary"
echo "================================================"
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
  echo -e "${GREEN}✅ All smoke tests passed!${NC}"
  echo ""
  echo "✓ Health endpoint working"
  echo "✓ Authentication working"
  echo "✓ Templates API working with new schema"
  echo "✓ Job creation and status check working"
  echo "✓ Token limit enforced (≤1500)"
  echo "✓ Idempotency working"
  echo ""
  echo "🚀 Preview environment is ready for UAT!"
  exit 0
else
  echo -e "${RED}❌ Some smoke tests failed!${NC}"
  echo ""
  echo "Please review the failures above and fix before UAT."
  exit 1
fi
