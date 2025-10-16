# API Curl Examples

Complete curl examples for all tepure API endpoints with error responses.

## Base URL

```bash
# Local development
export API_BASE="http://localhost:5000/api/v1"

# Production
export API_BASE="https://tepure-api-xxxxxxxxxx.run.app/api/v1"
```

---

## Authentication

### 1. Login

**Request:**
```bash
curl -X POST "${API_BASE}/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }'
```

**Success Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 900
}
```

**Error Response (401 - Invalid Credentials):**
```json
{
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "Invalid email or password",
    "hint": "Check your credentials and try again"
  }
}
```

**Error Response (400 - Validation Error):**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "hint": "Check request body and query parameters",
    "meta": {
      "details": [
        {
          "loc": ["email"],
          "msg": "field required",
          "type": "value_error.missing"
        }
      ]
    }
  }
}
```

### 2. Refresh Token

**Request:**
```bash
curl -X POST "${API_BASE}/auth/refresh" \
  -H "Authorization: Bearer ${REFRESH_TOKEN}"
```

**Success Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 900
}
```

**Error Response (401 - Token Expired):**
```json
{
  "error": {
    "code": "TOKEN_EXPIRED",
    "message": "Access token expired",
    "hint": "Refresh your token using /auth/refresh"
  }
}
```

### 3. Logout

**Request:**
```bash
curl -X POST "${API_BASE}/auth/logout" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"
```

**Success Response (200):**
```json
{
  "message": "Logged out successfully"
}
```

---

## Templates

### 4. List Templates

**Request:**
```bash
curl -X GET "${API_BASE}/templates?page=1&size=20&tag=marketing" \
  -H "Content-Type: application/json"
```

**Success Response (200):**
```json
{
  "templates": [
    {
      "id": "tpl_20250116120000",
      "name": "Instagram Story Template",
      "figma_file_key": "abc123xyz",
      "figma_node_id": "1:234",
      "category": "SNS",
      "tags": ["instagram", "story", "marketing"],
      "preview_url": "https://example.com/preview.png",
      "fields": [
        {
          "type": "text",
          "label": "Title",
          "default_value": "Your Title Here"
        },
        {
          "type": "color",
          "label": "Background Color",
          "default_value": "#FF5733"
        }
      ],
      "version": "1.0.0",
      "created_at": "2025-01-16T12:00:00Z"
    }
  ],
  "total": 50,
  "page": 1,
  "size": 20,
  "has_next": true
}
```

### 5. Get Template by ID

**Request:**
```bash
curl -X GET "${API_BASE}/templates/tpl_20250116120000" \
  -H "Content-Type: application/json"
```

**Success Response (200):**
```json
{
  "id": "tpl_20250116120000",
  "name": "Instagram Story Template",
  "figma_file_key": "abc123xyz",
  "figma_node_id": "1:234",
  "category": "SNS",
  "tags": ["instagram", "story"],
  "preview_url": "https://example.com/preview.png",
  "fields": [
    {
      "type": "text",
      "label": "Title",
      "default_value": "Your Title Here"
    }
  ],
  "version": "1.0.0",
  "created_at": "2025-01-16T12:00:00Z"
}
```

**Error Response (404 - Not Found):**
```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Template not found",
    "hint": "Check the ID and try again"
  }
}
```

### 6. Create Template (Admin Only)

**Request:**
```bash
curl -X POST "${API_BASE}/templates" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "New LP Template",
    "figma_file_key": "xyz789abc",
    "figma_node_id": "1:456",
    "category": "LP",
    "tags": ["landing-page", "marketing"],
    "preview_url": "https://example.com/new-preview.png",
    "fields": [
      {
        "type": "text",
        "label": "Headline",
        "default_value": "Welcome"
      },
      {
        "type": "color",
        "label": "Primary Color",
        "default_value": "#4A90E2"
      }
    ]
  }'
```

**Success Response (201):**
```json
{
  "id": "tpl_20250116130000",
  "name": "New LP Template",
  "figma_file_key": "xyz789abc",
  "category": "LP",
  "created_at": "2025-01-16T13:00:00Z"
}
```

**Error Response (403 - Forbidden):**
```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "Access denied",
    "hint": "You don't have permission to access this resource"
  }
}
```

---

## Generation Jobs

### 7. Create Generation Job (with Idempotency)

**Request:**
```bash
curl -X POST "${API_BASE}/use" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -H "X-Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000" \
  -d '{
    "template_id": "tpl_20250116120000",
    "inputs": {
      "title": "Summer Sale 2025",
      "description": "Up to 50% off on all items",
      "background_color": "#FF6B6B"
    },
    "temperature": 0.7,
    "intensity": "medium"
  }'
```

**Success Response (202 - Accepted):**
```json
{
  "job_id": "job_20250116140000",
  "status": "pending",
  "result": null,
  "error": null,
  "usage": null
}
```

**Error Response (422 - Token Budget Exceeded):**
```json
{
  "error": {
    "code": "TOKEN_BUDGET_EXCEEDED",
    "message": "Token budget exceeded: 1200 > 900",
    "hint": "Reduce input size or simplify the request",
    "meta": {
      "estimated_tokens": 1200,
      "budget_tokens": 900,
      "agent": "Agent1"
    }
  }
}
```

**Error Response (429 - Quota Exceeded):**
```json
{
  "error": {
    "code": "QUOTA_EXCEEDED",
    "message": "Monthly quota exceeded: 50/50",
    "hint": "Wait until next month or upgrade plan",
    "meta": {
      "usage": 50,
      "quota": 50
    }
  }
}
```

**Error Response (429 - Rate Limit):**
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded: 5 requests per minute",
    "hint": "Wait before retrying",
    "meta": {
      "limit": 5,
      "window": "minute"
    }
  }
}
```

**Error Response (409 - Idempotency Conflict):**
```json
{
  "error": {
    "code": "IDEMPOTENCY_CONFLICT",
    "message": "Request with same idempotency key already exists",
    "hint": "Use existing job_id: job_20250116140000",
    "meta": {
      "idempotency_key": "550e8400-e29b-41d4-a716-446655440000",
      "existing_job_id": "job_20250116140000"
    }
  }
}
```

### 8. Get Job Status

**Request:**
```bash
curl -X GET "${API_BASE}/jobs/job_20250116140000" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"
```

**Success Response (200 - Pending):**
```json
{
  "job_id": "job_20250116140000",
  "status": "pending",
  "result": null,
  "error": null,
  "usage": null
}
```

**Success Response (200 - Processing):**
```json
{
  "job_id": "job_20250116140000",
  "status": "processing",
  "result": null,
  "error": null,
  "usage": null
}
```

**Success Response (200 - Completed):**
```json
{
  "job_id": "job_20250116140000",
  "status": "completed",
  "result": {
    "title": "Summer Sale 2025 - Limited Time Offer",
    "description": "Don't miss out! Get up to 50% off on all summer items. Hurry, sale ends soon!",
    "background_color": "#FF6B6B"
  },
  "error": null,
  "usage": {
    "prompt_tokens": 450,
    "completion_tokens": 380,
    "total_tokens": 830,
    "cost_usd": 0.007425
  }
}
```

**Success Response (200 - Failed):**
```json
{
  "job_id": "job_20250116140000",
  "status": "failed",
  "result": null,
  "error": "LLM API rate limit exceeded",
  "usage": null
}
```

**Error Response (404 - Job Not Found):**
```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Job not found",
    "hint": "Check the ID and try again"
  }
}
```

**Error Response (403 - Forbidden):**
```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "You don't have permission to access this job",
    "hint": "You don't have permission to access this resource"
  }
}
```

---

## Admin Endpoints

### 9. Get Metrics (Admin Only)

**Request:**
```bash
curl -X GET "${API_BASE}/metrics" \
  -H "Authorization: Bearer ${ADMIN_ACCESS_TOKEN}"
```

**Success Response (200):**
```json
{
  "success_rate": 0.95,
  "average_latency_ms": 1234.5,
  "daily_generation_count": 100,
  "total_cost_usd": 5.67,
  "error_rate": 0.02,
  "p95_latency_ms": 1850
}
```

### 10. Get Audit Logs (Admin Only)

**Request:**
```bash
curl -X GET "${API_BASE}/auditlogs?user=usr_123&from=2025-01-01&to=2025-01-31&page=1&size=20" \
  -H "Authorization: Bearer ${ADMIN_ACCESS_TOKEN}"
```

**Success Response (200):**
```json
{
  "logs": [
    {
      "timestamp": "2025-01-16T14:30:00Z",
      "user_id": "usr_123",
      "action": "job.created",
      "entity_type": "job",
      "entity_id": "job_20250116140000",
      "ip_address": "203.0.113.45",
      "latency_ms": 125
    }
  ],
  "total": 150,
  "page": 1,
  "size": 20
}
```

---

## Health Check

### 11. Health Check

**Request:**
```bash
curl -X GET "${API_BASE}/../health"
```

**Success Response (200):**
```json
{
  "ok": true,
  "version": "1.0.0",
  "git": "a1b2c3d"
}
```

---

## Common Error Responses

### 400 - Bad Request (Invalid JSON)

```json
{
  "error": {
    "code": "INVALID_JSON",
    "message": "Invalid JSON payload",
    "hint": "Ensure request body is valid JSON"
  }
}
```

### 401 - Unauthorized (Token Invalid)

```json
{
  "error": {
    "code": "TOKEN_INVALID",
    "message": "Invalid access token",
    "hint": "Refresh your token using /auth/refresh"
  }
}
```

### 500 - Internal Server Error

```json
{
  "error": {
    "code": "INTERNAL_SERVER_ERROR",
    "message": "Internal server error",
    "hint": "Contact support if this persists"
  }
}
```

### 503 - Service Unavailable

```json
{
  "error": {
    "code": "SERVICE_UNAVAILABLE",
    "message": "Service temporarily unavailable",
    "hint": "Try again later"
  }
}
```

---

## Testing Scripts

### Full Flow Test

```bash
#!/bin/bash
set -e

API_BASE="http://localhost:5000/api/v1"

echo "1. Login..."
LOGIN_RESPONSE=$(curl -s -X POST "${API_BASE}/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }')

ACCESS_TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')
echo "Access Token: ${ACCESS_TOKEN:0:20}..."

echo ""
echo "2. List Templates..."
curl -s -X GET "${API_BASE}/templates?page=1&size=5" | jq '.'

echo ""
echo "3. Create Job..."
JOB_RESPONSE=$(curl -s -X POST "${API_BASE}/use" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -H "X-Idempotency-Key: $(uuidgen)" \
  -d '{
    "template_id": "tpl_20250116120000",
    "inputs": {
      "title": "Test Title",
      "description": "Test Description"
    },
    "temperature": 0.7,
    "intensity": "medium"
  }')

JOB_ID=$(echo $JOB_RESPONSE | jq -r '.job_id')
echo "Job ID: ${JOB_ID}"

echo ""
echo "4. Check Job Status..."
curl -s -X GET "${API_BASE}/jobs/${JOB_ID}" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" | jq '.'

echo ""
echo "Test complete!"
```

---

## Notes

1. **Idempotency Keys**: Use UUIDs for idempotency keys. Same key returns same job.
2. **Rate Limits**:
   - Global: 30 requests/min
   - Per-user: 5 requests/min
   - Monthly: 50 jobs/user
3. **Token Budgets**:
   - Total: 1,500 tokens/job
   - Agent1: 900 tokens
   - Agent2: 600 tokens
4. **Authentication**: Access tokens expire in 15 minutes, refresh tokens in 7 days.
