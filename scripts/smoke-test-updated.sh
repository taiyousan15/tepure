#!/usr/bin/env bash
#
# Smoke Test Script (Updated 2025-10-16)
# ========================================
# Tests critical functionality after deployment
#
# Usage:
#   export API_BASE="https://tepure-api-preview-xxx.run.app"
#   bash scripts/smoke-test-updated.sh
#

set -euo pipefail

: "${API_BASE:?ERROR: API_BASE environment variable must be set}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASS_COUNT=0
FAIL_COUNT=0

pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASS_COUNT++))
}

fail() {
    echo -e "${RED}✗${NC} $1"
    ((FAIL_COUNT++))
}

warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

echo "=================================================="
echo "Smoke Test - tepure API"
echo "API Base: $API_BASE"
echo "Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=================================================="
echo ""

# ========== Test 1: Health Check ==========
echo "Test 1: Health Check"
HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" "${API_BASE}/health")
HEALTH_BODY=$(echo "$HEALTH_RESPONSE" | head -n -1)
HEALTH_CODE=$(echo "$HEALTH_RESPONSE" | tail -n 1)

if [ "$HEALTH_CODE" -eq 200 ]; then
    OK=$(echo "$HEALTH_BODY" | jq -r '.ok')
    VERSION=$(echo "$HEALTH_BODY" | jq -r '.version')
    GIT=$(echo "$HEALTH_BODY" | jq -r '.git')

    if [ "$OK" == "true" ] && [ -n "$VERSION" ] && [ -n "$GIT" ] && [ "$GIT" != "null" ]; then
        pass "Health endpoint returns 200 with ok=true, version=$VERSION, git=$GIT"

        # Check for extra keys (should only have ok, version, git)
        KEY_COUNT=$(echo "$HEALTH_BODY" | jq 'keys | length')
        if [ "$KEY_COUNT" -eq 3 ]; then
            pass "Health endpoint returns exactly 3 keys (ok, version, git)"
        else
            warn "Health endpoint returns $KEY_COUNT keys (expected 3)"
        fi
    else
        fail "Health endpoint missing required fields (ok=$OK, version=$VERSION, git=$GIT)"
    fi
else
    fail "Health endpoint returned $HEALTH_CODE (expected 200)"
fi

echo ""

# ========== Test 2: Login ==========
echo "Test 2: Authentication - Login"
LOGIN_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${API_BASE}/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"email":"test@example.com","password":"password123"}')

LOGIN_BODY=$(echo "$LOGIN_RESPONSE" | head -n -1)
LOGIN_CODE=$(echo "$LOGIN_RESPONSE" | tail -n 1)

if [ "$LOGIN_CODE" -eq 200 ]; then
    ACCESS_TOKEN=$(echo "$LOGIN_BODY" | jq -r '.access_token')

    if [ -n "$ACCESS_TOKEN" ] && [ "$ACCESS_TOKEN" != "null" ]; then
        pass "Login successful, access_token received"
    else
        fail "Login returned 200 but no access_token"
        echo "Exiting - cannot proceed without authentication"
        exit 1
    fi
else
    fail "Login failed with code $LOGIN_CODE"
    echo "Response: $LOGIN_BODY"
    echo "Exiting - cannot proceed without authentication"
    exit 1
fi

echo ""

# ========== Test 3: List Templates ==========
echo "Test 3: List Templates"
TEMPLATES_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "${API_BASE}/api/v1/templates" \
    -H "Authorization: Bearer ${ACCESS_TOKEN}")

TEMPLATES_BODY=$(echo "$TEMPLATES_RESPONSE" | head -n -1)
TEMPLATES_CODE=$(echo "$TEMPLATES_RESPONSE" | tail -n 1)

if [ "$TEMPLATES_CODE" -eq 200 ]; then
    TEMPLATES=$(echo "$TEMPLATES_BODY" | jq -r '.templates')
    TEMPLATE_COUNT=$(echo "$TEMPLATES_BODY" | jq -r '.templates | length')

    if [ "$TEMPLATE_COUNT" -ge 3 ]; then
        pass "Templates list returned $TEMPLATE_COUNT templates (≥3)"

        # Get first template ID for next tests
        TEMPLATE_ID=$(echo "$TEMPLATES_BODY" | jq -r '.templates[0].id')
        pass "Using template_id=$TEMPLATE_ID for job creation tests"
    else
        fail "Templates list returned only $TEMPLATE_COUNT templates (expected ≥3)"
    fi
else
    fail "List templates failed with code $TEMPLATES_CODE"
fi

echo ""

# ========== Test 4: Create Job (with Idempotency) ==========
echo "Test 4: Create Generation Job (with Idempotency-Key)"
IDEMPOTENCY_KEY="smoke-test-$(date +%s)-$$"

JOB_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${API_BASE}/api/v1/use" \
    -H "Authorization: Bearer ${ACCESS_TOKEN}" \
    -H "Content-Type: application/json" \
    -H "Idempotency-Key: ${IDEMPOTENCY_KEY}" \
    -d "{
        \"template_id\": \"${TEMPLATE_ID}\",
        \"inputs\": {
            \"title\": \"Smoke Test Title\",
            \"description\": \"Smoke Test Description\"
        },
        \"temperature\": 0.7,
        \"intensity\": 7
    }")

JOB_BODY=$(echo "$JOB_RESPONSE" | head -n -1)
JOB_CODE=$(echo "$JOB_RESPONSE" | tail -n 1)

if [ "$JOB_CODE" -eq 202 ]; then
    JOB_ID=$(echo "$JOB_BODY" | jq -r '.job_id')
    JOB_STATUS=$(echo "$JOB_BODY" | jq -r '.status')

    if [ -n "$JOB_ID" ] && [ "$JOB_ID" != "null" ]; then
        pass "Job created successfully: $JOB_ID (status=$JOB_STATUS)"
    else
        fail "Job creation returned 202 but no job_id"
    fi
elif [ "$JOB_CODE" -eq 422 ]; then
    ERROR_CODE=$(echo "$JOB_BODY" | jq -r '.error.code')
    if [ "$ERROR_CODE" == "TOKEN_BUDGET_EXCEEDED" ]; then
        warn "Job creation returned 422 TOKEN_BUDGET_EXCEEDED (expected if input is large)"
    else
        fail "Job creation returned 422 with unexpected error: $ERROR_CODE"
    fi
elif [ "$JOB_CODE" -eq 429 ]; then
    warn "Job creation returned 429 (rate limited - expected if running tests repeatedly)"
else
    fail "Job creation failed with code $JOB_CODE"
    echo "Response: $JOB_BODY"
fi

echo ""

# ========== Test 5: Idempotency Check ==========
if [ -n "$JOB_ID" ] && [ "$JOB_ID" != "null" ]; then
    echo "Test 5: Idempotency - Duplicate Request"

    JOB2_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${API_BASE}/api/v1/use" \
        -H "Authorization: Bearer ${ACCESS_TOKEN}" \
        -H "Content-Type: application/json" \
        -H "Idempotency-Key: ${IDEMPOTENCY_KEY}" \
        -d "{
            \"template_id\": \"${TEMPLATE_ID}\",
            \"inputs\": {
                \"title\": \"Smoke Test Title\",
                \"description\": \"Smoke Test Description\"
            },
            \"temperature\": 0.7,
            \"intensity\": 7
        }")

    JOB2_BODY=$(echo "$JOB2_RESPONSE" | head -n -1)
    JOB2_CODE=$(echo "$JOB2_RESPONSE" | tail -n 1)

    if [ "$JOB2_CODE" -eq 202 ]; then
        JOB2_ID=$(echo "$JOB2_BODY" | jq -r '.job_id')

        if [ "$JOB2_ID" == "$JOB_ID" ]; then
            pass "Idempotency working: same job_id returned ($JOB_ID)"
        else
            fail "Idempotency NOT working: different job_ids ($JOB_ID vs $JOB2_ID)"
        fi
    else
        fail "Duplicate request with same Idempotency-Key failed with code $JOB2_CODE"
    fi

    echo ""
fi

# ========== Test 6: Check Job Status ==========
if [ -n "$JOB_ID" ] && [ "$JOB_ID" != "null" ]; then
    echo "Test 6: Check Job Status"

    sleep 2  # Wait a bit for job to process

    STATUS_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "${API_BASE}/api/v1/jobs/${JOB_ID}" \
        -H "Authorization: Bearer ${ACCESS_TOKEN}")

    STATUS_BODY=$(echo "$STATUS_RESPONSE" | head -n -1)
    STATUS_CODE=$(echo "$STATUS_RESPONSE" | tail -n 1)

    if [ "$STATUS_CODE" -eq 200 ]; then
        CURRENT_STATUS=$(echo "$STATUS_BODY" | jq -r '.status')
        pass "Job status retrieved: $CURRENT_STATUS"

        # Check if status is valid
        if [[ "$CURRENT_STATUS" =~ ^(pending|processing|completed|failed)$ ]]; then
            pass "Job status is valid: $CURRENT_STATUS"
        else
            fail "Job status is invalid: $CURRENT_STATUS"
        fi
    else
        fail "Get job status failed with code $STATUS_CODE"
    fi

    echo ""
fi

# ========== Test 7: Token Budget Exceeded (422) ==========
echo "Test 7: Token Budget Exceeded (422 Error)"

# Generate large input to exceed token budget
LARGE_TEXT=$(python3 -c "print('A' * 12000)")

TOKEN_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${API_BASE}/api/v1/use" \
    -H "Authorization: Bearer ${ACCESS_TOKEN}" \
    -H "Content-Type: application/json" \
    -H "Idempotency-Key: smoke-token-exceeded-$(date +%s)" \
    -d "{
        \"template_id\": \"${TEMPLATE_ID}\",
        \"inputs\": {
            \"title\": \"${LARGE_TEXT}\"
        },
        \"temperature\": 1.0,
        \"intensity\": 10
    }")

TOKEN_BODY=$(echo "$TOKEN_RESPONSE" | head -n -1)
TOKEN_CODE=$(echo "$TOKEN_RESPONSE" | tail -n 1)

if [ "$TOKEN_CODE" -eq 422 ]; then
    ERROR_CODE=$(echo "$TOKEN_BODY" | jq -r '.error.code')
    ERROR_MESSAGE=$(echo "$TOKEN_BODY" | jq -r '.error.message')

    if [ "$ERROR_CODE" == "TOKEN_BUDGET_EXCEEDED" ]; then
        pass "422 TOKEN_BUDGET_EXCEEDED error correctly returned"
        pass "Error message: $ERROR_MESSAGE"

        # Check error format
        HAS_HINT=$(echo "$TOKEN_BODY" | jq -r '.error.hint')
        HAS_META=$(echo "$TOKEN_BODY" | jq -r '.error.meta')

        if [ -n "$HAS_HINT" ] && [ "$HAS_HINT" != "null" ]; then
            pass "Error includes hint field"
        fi

        if [ -n "$HAS_META" ] && [ "$HAS_META" != "null" ]; then
            pass "Error includes meta field"
        fi
    else
        fail "422 returned but with wrong error code: $ERROR_CODE (expected TOKEN_BUDGET_EXCEEDED)"
    fi
else
    warn "Large input did not trigger 422 (got $TOKEN_CODE) - token estimation may need tuning"
fi

echo ""

# ========== Test 8: Rate Limiting (429) ==========
echo "Test 8: Rate Limiting (429 Error)"
echo "Sending 6 rapid requests to trigger rate limit..."

RATE_LIMIT_HIT=false

for i in {1..6}; do
    RATE_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${API_BASE}/api/v1/use" \
        -H "Authorization: Bearer ${ACCESS_TOKEN}" \
        -H "Content-Type: application/json" \
        -H "Idempotency-Key: rate-test-$i-$(date +%s)" \
        -d "{
            \"template_id\": \"${TEMPLATE_ID}\",
            \"inputs\": {
                \"title\": \"Rate Limit Test $i\"
            },
            \"temperature\": 0.5,
            \"intensity\": 5
        }")

    RATE_CODE=$(echo "$RATE_RESPONSE" | tail -n 1)

    if [ "$RATE_CODE" -eq 429 ]; then
        RATE_LIMIT_HIT=true
        RATE_BODY=$(echo "$RATE_RESPONSE" | head -n -1)
        ERROR_CODE=$(echo "$RATE_BODY" | jq -r '.error.code')

        if [[ "$ERROR_CODE" == "RATE_LIMIT_EXCEEDED" ]] || [[ "$ERROR_CODE" == "QUOTA_EXCEEDED" ]]; then
            pass "429 rate limit triggered on request #$i (error=$ERROR_CODE)"
            break
        fi
    fi
done

if [ "$RATE_LIMIT_HIT" = false ]; then
    warn "Rate limit not triggered after 6 requests - limit may be higher than 5 req/min"
fi

echo ""

# ========== Summary ==========
echo "=================================================="
echo "Test Summary"
echo "=================================================="
echo -e "${GREEN}Passed:${NC} $PASS_COUNT"
echo -e "${RED}Failed:${NC} $FAIL_COUNT"

if [ $FAIL_COUNT -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ All smoke tests passed!${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}✗ Some tests failed. Please review above.${NC}"
    exit 1
fi
