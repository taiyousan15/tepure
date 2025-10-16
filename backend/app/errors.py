"""
Unified error format and custom exceptions

Standard error format:
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "hint": "Optional hint for resolution",
    "meta": {
      "key": "value"  // Optional metadata
    }
  }
}
"""
from typing import Optional, Dict, Any, Tuple
from flask import jsonify


# ========== Error Codes ==========

# 400 Bad Request
ERROR_VALIDATION_ERROR = "VALIDATION_ERROR"
ERROR_INVALID_JSON = "INVALID_JSON"

# 401 Unauthorized
ERROR_INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
ERROR_TOKEN_EXPIRED = "TOKEN_EXPIRED"
ERROR_TOKEN_INVALID = "TOKEN_INVALID"

# 403 Forbidden
ERROR_FORBIDDEN = "FORBIDDEN"
ERROR_ADMIN_REQUIRED = "ADMIN_REQUIRED"

# 404 Not Found
ERROR_NOT_FOUND = "NOT_FOUND"
ERROR_TEMPLATE_NOT_FOUND = "TEMPLATE_NOT_FOUND"
ERROR_JOB_NOT_FOUND = "JOB_NOT_FOUND"

# 409 Conflict
ERROR_IDEMPOTENCY_CONFLICT = "IDEMPOTENCY_CONFLICT"
ERROR_ALREADY_EXISTS = "ALREADY_EXISTS"

# 422 Unprocessable Entity
ERROR_TOKEN_BUDGET_EXCEEDED = "TOKEN_BUDGET_EXCEEDED"
ERROR_INVALID_PARAMETERS = "INVALID_PARAMETERS"

# 429 Too Many Requests
ERROR_RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
ERROR_QUOTA_EXCEEDED = "QUOTA_EXCEEDED"

# 500 Internal Server Error
ERROR_INTERNAL_SERVER = "INTERNAL_SERVER_ERROR"
ERROR_LLM_API_ERROR = "LLM_API_ERROR"
ERROR_SHEETS_API_ERROR = "SHEETS_API_ERROR"

# 503 Service Unavailable
ERROR_SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
ERROR_LLM_UNAVAILABLE = "LLM_UNAVAILABLE"


# ========== Custom Exceptions ==========

class TepureError(Exception):
    """Base exception for tepure errors"""
    def __init__(
        self,
        code: str,
        message: str,
        hint: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None,
        status_code: int = 500
    ):
        self.code = code
        self.message = message
        self.hint = hint
        self.meta = meta or {}
        self.status_code = status_code
        super().__init__(message)


class TokenBudgetExceededError(TepureError):
    """Raised when token budget is exceeded"""
    def __init__(
        self,
        estimated_tokens: int,
        budget_tokens: int,
        agent: str = "unknown"
    ):
        super().__init__(
            code=ERROR_TOKEN_BUDGET_EXCEEDED,
            message=f"Token budget exceeded: {estimated_tokens} > {budget_tokens}",
            hint="Reduce input size or simplify the request",
            meta={
                "estimated_tokens": estimated_tokens,
                "budget_tokens": budget_tokens,
                "agent": agent
            },
            status_code=422
        )


class IdempotencyConflictError(TepureError):
    """Raised when idempotency key conflict detected"""
    def __init__(self, idempotency_key: str, existing_job_id: str):
        super().__init__(
            code=ERROR_IDEMPOTENCY_CONFLICT,
            message="Request with same idempotency key already exists",
            hint=f"Use existing job_id: {existing_job_id}",
            meta={
                "idempotency_key": idempotency_key,
                "existing_job_id": existing_job_id
            },
            status_code=409
        )


class QuotaExceededError(TepureError):
    """Raised when monthly quota is exceeded"""
    def __init__(self, usage: int, quota: int):
        super().__init__(
            code=ERROR_QUOTA_EXCEEDED,
            message=f"Monthly quota exceeded: {usage}/{quota}",
            hint="Wait until next month or upgrade plan",
            meta={
                "usage": usage,
                "quota": quota
            },
            status_code=429
        )


class RateLimitExceededError(TepureError):
    """Raised when rate limit is exceeded"""
    def __init__(self, limit: int, window: str = "minute"):
        super().__init__(
            code=ERROR_RATE_LIMIT_EXCEEDED,
            message=f"Rate limit exceeded: {limit} requests per {window}",
            hint="Wait before retrying",
            meta={
                "limit": limit,
                "window": window
            },
            status_code=429
        )


# ========== Error Response Helpers ==========

def format_error(
    code: str,
    message: str,
    hint: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Format error response in standard format

    Args:
        code: Error code
        message: Human-readable message
        hint: Optional hint for resolution
        meta: Optional metadata

    Returns:
        Error response dict
    """
    error_body = {
        "code": code,
        "message": message
    }

    if hint:
        error_body["hint"] = hint

    if meta:
        error_body["meta"] = meta

    return {"error": error_body}


def error_response(
    code: str,
    message: str,
    status_code: int,
    hint: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None
) -> Tuple[Any, int]:
    """
    Create error response tuple for Flask

    Args:
        code: Error code
        message: Human-readable message
        status_code: HTTP status code
        hint: Optional hint
        meta: Optional metadata

    Returns:
        Tuple of (jsonify response, status_code)
    """
    return jsonify(format_error(code, message, hint, meta)), status_code


def exception_to_response(exc: TepureError) -> Tuple[Any, int]:
    """
    Convert TepureError exception to Flask response

    Args:
        exc: TepureError exception

    Returns:
        Tuple of (jsonify response, status_code)
    """
    return error_response(
        code=exc.code,
        message=exc.message,
        status_code=exc.status_code,
        hint=exc.hint,
        meta=exc.meta
    )


# ========== Standard Error Responses ==========

def validation_error(details: Any = None) -> Tuple[Any, int]:
    """400 Validation Error"""
    return error_response(
        code=ERROR_VALIDATION_ERROR,
        message="Invalid request parameters",
        status_code=400,
        hint="Check request body and query parameters",
        meta={"details": details} if details else None
    )


def invalid_json_error() -> Tuple[Any, int]:
    """400 Invalid JSON"""
    return error_response(
        code=ERROR_INVALID_JSON,
        message="Invalid JSON payload",
        status_code=400,
        hint="Ensure request body is valid JSON"
    )


def invalid_credentials_error() -> Tuple[Any, int]:
    """401 Invalid Credentials"""
    return error_response(
        code=ERROR_INVALID_CREDENTIALS,
        message="Invalid email or password",
        status_code=401,
        hint="Check your credentials and try again"
    )


def token_expired_error() -> Tuple[Any, int]:
    """401 Token Expired"""
    return error_response(
        code=ERROR_TOKEN_EXPIRED,
        message="Access token expired",
        status_code=401,
        hint="Refresh your token using /auth/refresh"
    )


def forbidden_error(reason: Optional[str] = None) -> Tuple[Any, int]:
    """403 Forbidden"""
    return error_response(
        code=ERROR_FORBIDDEN,
        message=reason or "Access denied",
        status_code=403,
        hint="You don't have permission to access this resource"
    )


def not_found_error(resource: str = "Resource") -> Tuple[Any, int]:
    """404 Not Found"""
    return error_response(
        code=ERROR_NOT_FOUND,
        message=f"{resource} not found",
        status_code=404,
        hint="Check the ID and try again"
    )


def internal_server_error(details: Optional[str] = None) -> Tuple[Any, int]:
    """500 Internal Server Error"""
    return error_response(
        code=ERROR_INTERNAL_SERVER,
        message="Internal server error",
        status_code=500,
        hint="Contact support if this persists",
        meta={"details": details} if details else None
    )
