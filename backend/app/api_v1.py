"""
API v1 Blueprint - All REST endpoints
"""
import time
import structlog
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from pydantic import ValidationError
from datetime import datetime

from .auth import (
    hash_password,
    verify_password,
    create_access_token_for_user,
    create_refresh_token_for_user,
    require_auth,
    require_admin,
    mask_pii
)
from .schemas import (
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    TemplateCreateRequest,
    TemplateUpdateRequest,
    JobCreateRequest,
    ErrorResponse
)
from .sheets import GoogleSheetsClient
from .jobs import job_queue
from .agents import Agent1, Agent2, calculate_cost
from .metrics import metrics_collector
from .errors import (
    TepureError,
    TokenBudgetExceededError,
    IdempotencyConflictError,
    QuotaExceededError,
    exception_to_response,
    validation_error,
    invalid_json_error,
    invalid_credentials_error,
    forbidden_error,
    not_found_error,
    internal_server_error
)

logger = structlog.get_logger()

# Create blueprint
api_v1_bp = Blueprint('api_v1', __name__)

# Initialize services
sheets_client = GoogleSheetsClient()
agent1 = Agent1()
agent2 = Agent2()


# ========== Helper Functions ==========

def get_client_ip() -> str:
    """Get client IP address from request"""
    return request.headers.get('X-Forwarded-For', request.remote_addr)


def validate_request_json(schema_class):
    """Decorator to validate request JSON with Pydantic schema"""
    def decorator(f):
        def wrapper(*args, **kwargs):
            try:
                data = request.get_json()
                validated = schema_class(**data)
                request.validated_data = validated
                return f(*args, **kwargs)
            except ValidationError as e:
                logger.warning("validation_error", errors=e.errors())
                return jsonify({
                    'code': 'VALIDATION_ERROR',
                    'message': 'Invalid request parameters',
                    'details': e.errors()
                }), 400
            except Exception as e:
                logger.error("validation_exception", error=str(e))
                return jsonify({
                    'code': 'INVALID_JSON',
                    'message': 'Invalid JSON payload'
                }), 400
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator


# ========== Authentication Endpoints ==========

@api_v1_bp.route('/auth/login', methods=['POST'])
@current_app.limiter.limit("10 per minute")
def login():
    """
    User login endpoint

    Request:
        {
            "email": "user@example.com",
            "password": "password123"
        }

    Response:
        {
            "access_token": "...",
            "refresh_token": "...",
            "token_type": "Bearer",
            "expires_in": 900
        }
    """
    start_time = time.time()

    try:
        data = LoginRequest(**request.get_json())

        # Get user by email
        user = sheets_client.get_user_by_email(data.email)

        if not user or not verify_password(data.password, user['password_hash']):
            logger.warning("login_failed", email=mask_pii({'email': data.email}))
            return invalid_credentials_error()

        # Create tokens
        access_token = create_access_token_for_user(user['id'], user.get('role', 'user'))
        refresh_token = create_refresh_token_for_user(user['id'])

        # Log audit
        metrics_collector.write_audit_log(
            user_id=user['id'],
            action='auth.login',
            entity_type='user',
            entity_id=user['id'],
            ip_address=get_client_ip(),
            latency_ms=int((time.time() - start_time) * 1000)
        )

        logger.info("login_success", user_id=user['id'])

        return jsonify({
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'expires_in': 900
        }), 200

    except ValidationError as e:
        return validation_error(details=e.errors())
    except TepureError as e:
        return exception_to_response(e)
    except Exception as e:
        logger.error("login_error", error=str(e), exc_info=True)
        return internal_server_error()


@api_v1_bp.route('/auth/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """
    Refresh access token

    Request:
        Header: Authorization: Bearer <refresh_token>

    Response:
        {
            "access_token": "...",
            "token_type": "Bearer",
            "expires_in": 900
        }
    """
    try:
        user_id = get_jwt_identity()
        jwt_data = get_jwt()
        role = jwt_data.get('role', 'user')

        access_token = create_access_token_for_user(user_id, role)

        logger.info("token_refreshed", user_id=user_id)

        return jsonify({
            'access_token': access_token,
            'token_type': 'Bearer',
            'expires_in': 900
        }), 200

    except Exception as e:
        logger.error("refresh_error", error=str(e))
        return jsonify({
            'code': 'REFRESH_ERROR',
            'message': 'Token refresh failed'
        }), 500


@api_v1_bp.route('/auth/logout', methods=['POST'])
@require_auth
def logout():
    """
    Logout endpoint (client should discard tokens)

    Response:
        {
            "message": "Logged out successfully"
        }
    """
    user_id = get_jwt_identity()
    logger.info("logout", user_id=user_id)

    return jsonify({
        'message': 'Logged out successfully'
    }), 200


# ========== Template Endpoints ==========

@api_v1_bp.route('/templates', methods=['GET'])
@current_app.limiter.limit("30 per minute")
def list_templates():
    """
    List templates with pagination and filtering

    Query params:
        - query: Search query
        - tag: Filter by tag
        - page: Page number (default 1)
        - size: Page size (default 20, max 100)

    Response:
        {
            "templates": [...],
            "total": 100,
            "page": 1,
            "size": 20,
            "has_next": true
        }
    """
    try:
        query = request.args.get('query', '')
        tag = request.args.get('tag', '')
        page = int(request.args.get('page', 1))
        size = min(int(request.args.get('size', 20)), 100)

        offset = (page - 1) * size

        # Get templates from sheets
        # TODO: Implement search and tag filtering
        templates = sheets_client.get_templates(limit=size, offset=offset)

        logger.info("templates_listed", count=len(templates), page=page)

        return jsonify({
            'templates': templates,
            'total': len(templates),  # Approximate
            'page': page,
            'size': size,
            'has_next': len(templates) == size
        }), 200

    except Exception as e:
        logger.error("list_templates_error", error=str(e))
        return jsonify({
            'code': 'LIST_ERROR',
            'message': 'Failed to list templates'
        }), 500


@api_v1_bp.route('/templates/<template_id>', methods=['GET'])
@current_app.limiter.limit("30 per minute")
def get_template(template_id: str):
    """
    Get template by ID

    Response:
        {
            "id": "tpl_123",
            "name": "Template Name",
            ...
        }
    """
    try:
        template = sheets_client.get_template(template_id)

        if not template:
            return not_found_error("Template")

        logger.info("template_retrieved", template_id=template_id)

        return jsonify(template), 200

    except TepureError as e:
        return exception_to_response(e)
    except Exception as e:
        logger.error("get_template_error", template_id=template_id, error=str(e))
        return internal_server_error()


@api_v1_bp.route('/templates', methods=['POST'])
@require_admin
def create_template():
    """
    Create new template (admin only)

    Request:
        {
            "name": "Template Name",
            "figma_file_key": "abc123",
            "category": "social-media",
            "tags": ["instagram", "story"]
        }

    Response:
        {
            "id": "tpl_123",
            "name": "Template Name",
            ...
        }
    """
    start_time = time.time()

    try:
        data = TemplateCreateRequest(**request.get_json())
        user_id = get_jwt_identity()

        # Create template
        template_id = sheets_client.create_template(data.dict())
        template = sheets_client.get_template(template_id)

        # Log audit
        metrics_collector.write_audit_log(
            user_id=user_id,
            action='template.created',
            entity_type='template',
            entity_id=template_id,
            ip_address=get_client_ip(),
            latency_ms=int((time.time() - start_time) * 1000)
        )

        logger.info("template_created", template_id=template_id, user_id=user_id)

        return jsonify(template), 201

    except ValidationError as e:
        return jsonify({
            'code': 'VALIDATION_ERROR',
            'message': 'Invalid request',
            'details': e.errors()
        }), 400
    except Exception as e:
        logger.error("create_template_error", error=str(e))
        return jsonify({
            'code': 'CREATE_ERROR',
            'message': 'Failed to create template'
        }), 500


# ========== Generation Endpoints ==========

@api_v1_bp.route('/use', methods=['POST'])
@require_auth
@current_app.limiter.limit("5 per minute")
def create_generation_job():
    """
    Create generation job with idempotency support

    Request:
        {
            "template_id": "tpl_123",
            "inputs": {"title": "Hello", "description": "World"},
            "temperature": 0.7,
            "intensity": "medium",
            "idempotency_key": "optional-uuid"
        }

    Response:
        {
            "job_id": "job_123",
            "status": "pending",
            ...
        }
    """
    start_time = time.time()

    try:
        data = JobCreateRequest(**request.get_json())
        user_id = get_jwt_identity()

        # Check monthly quota
        usage = sheets_client.get_user_monthly_usage(user_id)
        user = sheets_client.get_user_by_email(get_jwt()['email'])  # Get user for quota
        monthly_quota = user.get('monthly_quota', 100)

        if usage >= monthly_quota:
            logger.warning("quota_exceeded", user_id=user_id, usage=usage, quota=monthly_quota)
            raise QuotaExceededError(usage=usage, quota=monthly_quota)

        # Get idempotency key
        idempotency_key = data.idempotency_key or request.headers.get('X-Idempotency-Key')

        # Create job
        job_id = job_queue.create_job(
            user_id=user_id,
            template_id=data.template_id,
            inputs=data.inputs,
            temperature=data.temperature,
            intensity=data.intensity,
            idempotency_key=idempotency_key
        )

        # Get job status
        job = job_queue.get_job_status(job_id)

        # Log audit
        metrics_collector.write_audit_log(
            user_id=user_id,
            action='job.created',
            entity_type='job',
            entity_id=job_id,
            ip_address=get_client_ip(),
            latency_ms=int((time.time() - start_time) * 1000),
            metadata={'template_id': data.template_id}
        )

        logger.info("job_created", job_id=job_id, user_id=user_id, template_id=data.template_id)

        return jsonify(job), 202

    except ValidationError as e:
        return validation_error(details=e.errors())
    except TokenBudgetExceededError as e:
        # 422 Token Budget Exceeded
        logger.warning("token_budget_exceeded", user_id=user_id, error=str(e))
        return exception_to_response(e)
    except QuotaExceededError as e:
        # 429 Quota Exceeded
        return exception_to_response(e)
    except IdempotencyConflictError as e:
        # 409 Idempotency Conflict
        return exception_to_response(e)
    except TepureError as e:
        return exception_to_response(e)
    except Exception as e:
        logger.error("create_job_error", error=str(e), exc_info=True)
        return internal_server_error()


@api_v1_bp.route('/jobs/<job_id>', methods=['GET'])
@require_auth
def get_job(job_id: str):
    """
    Get job status and result

    Response:
        {
            "job_id": "job_123",
            "status": "completed",
            "result": {...},
            "usage": {...}
        }
    """
    try:
        user_id = get_jwt_identity()
        job = job_queue.get_job_status(job_id)

        if not job:
            return not_found_error("Job")

        # Check authorization
        if job['user_id'] != user_id and get_jwt().get('role') != 'admin':
            return forbidden_error("You don't have permission to access this job")

        logger.info("job_retrieved", job_id=job_id, status=job['status'])

        return jsonify(job), 200

    except TepureError as e:
        return exception_to_response(e)
    except Exception as e:
        logger.error("get_job_error", job_id=job_id, error=str(e))
        return internal_server_error()


# ========== Admin Endpoints ==========

@api_v1_bp.route('/metrics', methods=['GET'])
@require_admin
def get_metrics():
    """
    Get system metrics (admin only)

    Response:
        {
            "success_rate": 0.95,
            "average_latency_ms": 1234.5,
            "daily_generation_count": 100,
            ...
        }
    """
    try:
        metrics = metrics_collector.get_comprehensive_metrics()
        logger.info("metrics_retrieved")
        return jsonify(metrics), 200

    except Exception as e:
        logger.error("get_metrics_error", error=str(e))
        return jsonify({
            'code': 'METRICS_ERROR',
            'message': 'Failed to get metrics'
        }), 500


@api_v1_bp.route('/auditlogs', methods=['GET'])
@require_admin
def get_audit_logs():
    """
    Get audit logs (admin only)

    Query params:
        - user: Filter by user ID
        - from: Start date (ISO format)
        - to: End date (ISO format)
        - page: Page number
        - size: Page size

    Response:
        {
            "logs": [...],
            "total": 100,
            "page": 1,
            "size": 20
        }
    """
    try:
        user_id = request.args.get('user')
        from_date = request.args.get('from')
        to_date = request.args.get('to')
        page = int(request.args.get('page', 1))
        size = min(int(request.args.get('size', 20)), 100)

        offset = (page - 1) * size

        result = metrics_collector.get_audit_logs(
            user_id=user_id,
            from_date=from_date,
            to_date=to_date,
            limit=size,
            offset=offset
        )

        logger.info("audit_logs_retrieved", count=len(result['logs']))

        return jsonify(result), 200

    except Exception as e:
        logger.error("get_audit_logs_error", error=str(e))
        return jsonify({
            'code': 'AUDIT_LOGS_ERROR',
            'message': 'Failed to get audit logs'
        }), 500
