"""
Jobs API endpoints - Template fill job management
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.sheets import GoogleSheetsClient

bp = Blueprint('jobs', __name__)
sheets_client = GoogleSheetsClient()


@bp.route('', methods=['POST'])
@jwt_required()
def create_job():
    """
    Create a new template fill job

    Request body:
    {
        "template_id": "tpl_123",
        "input_data": {
            "HEAD_TITLE": "春の大セール開催中",
            "SUB_TITLE": "全商品30%OFF",
            "CTA_BUTTON": "今すぐチェック"
        }
    }

    Response:
    {
        "job_id": "job_abc123",
        "status": "pending",
        "template_id": "tpl_123",
        "created_at": "2025-10-16T12:00:00Z"
    }
    """
    data = request.get_json()

    if not data:
        return jsonify({
            'error': {
                'code': 'INVALID_REQUEST',
                'message': 'Request body is required'
            }
        }), 400

    # Validate required fields
    template_id = data.get('template_id')
    input_data = data.get('input_data')

    if not template_id:
        return jsonify({
            'error': {
                'code': 'MISSING_FIELD',
                'message': 'template_id is required'
            }
        }), 400

    if not input_data or not isinstance(input_data, dict):
        return jsonify({
            'error': {
                'code': 'INVALID_INPUT_DATA',
                'message': 'input_data must be a non-empty object'
            }
        }), 400

    # Get current user
    current_user = get_jwt_identity()

    # Verify template exists
    template = sheets_client.get_template(template_id)
    if not template:
        return jsonify({
            'error': {
                'code': 'TEMPLATE_NOT_FOUND',
                'message': f'Template {template_id} not found'
            }
        }), 404

    # Create job in Google Sheets
    try:
        # Get user ID from email (simplified - in production, query users table)
        user = sheets_client.get_user_by_email(current_user)
        user_id = user['id'] if user else current_user

        job_data = {
            'user_id': user_id,
            'template_id': template_id,
            'input_data': input_data
        }

        job_id = sheets_client.create_fill_job(job_data)

        # Log job creation
        sheets_client.log_audit(
            actor=current_user,
            action='job.created',
            target_id=job_id,
            metadata={
                'template_id': template_id,
                'template_name': template.get('name', 'Unknown'),
                'field_count': len(input_data)
            }
        )

        return jsonify({
            'job_id': job_id,
            'status': 'pending',
            'template_id': template_id,
            'template_name': template.get('name'),
            'message': 'Job created successfully. Open Figma plugin to apply changes.'
        }), 201

    except Exception as e:
        print(f"Error creating job: {e}")
        return jsonify({
            'error': {
                'code': 'JOB_CREATION_FAILED',
                'message': 'Failed to create job'
            }
        }), 500


@bp.route('', methods=['GET'])
@jwt_required()
def list_jobs():
    """
    List all jobs for current user

    Query parameters:
    - limit: Maximum number of jobs to return (default: 20)
    - offset: Number of jobs to skip (default: 0)
    - status: Filter by status (pending/completed/failed)

    Response:
    {
        "jobs": [
            {
                "job_id": "job_abc123",
                "template_id": "tpl_123",
                "status": "pending",
                "created_at": "2025-10-16T12:00:00Z"
            }
        ],
        "total": 10,
        "limit": 20,
        "offset": 0
    }
    """
    current_user = get_jwt_identity()
    limit = request.args.get('limit', 20, type=int)
    offset = request.args.get('offset', 0, type=int)
    status_filter = request.args.get('status', type=str)

    try:
        # Get user ID from email
        user = sheets_client.get_user_by_email(current_user)
        user_id = user['id'] if user else current_user

        # Get jobs from Google Sheets
        jobs = sheets_client.get_fill_jobs(user_id, limit, offset, status_filter)

        # Get total count for pagination
        all_jobs = sheets_client.get_fill_jobs(user_id, limit=10000, offset=0, status_filter=status_filter)
        total = len(all_jobs)

        return jsonify({
            'jobs': jobs,
            'total': total,
            'limit': limit,
            'offset': offset
        }), 200

    except Exception as e:
        print(f"Error listing jobs: {e}")
        return jsonify({
            'error': {
                'code': 'JOB_LIST_FAILED',
                'message': 'Failed to list jobs'
            }
        }), 500


@bp.route('/<job_id>', methods=['GET'])
@jwt_required()
def get_job(job_id):
    """
    Get job details

    Response:
    {
        "job_id": "job_abc123",
        "user_id": "usr_123",
        "template_id": "tpl_123",
        "status": "completed",
        "input_data": {...},
        "result_urls": ["https://..."],
        "created_at": "2025-10-16T12:00:00Z",
        "updated_at": "2025-10-16T12:05:00Z"
    }
    """
    # TODO: Implement job detail retrieval
    return jsonify({
        'error': {
            'code': 'NOT_IMPLEMENTED',
            'message': 'Job detail retrieval not yet implemented'
        }
    }), 501


@bp.route('/<job_id>', methods=['PATCH'])
@jwt_required()
def update_job(job_id):
    """
    Update job status (typically called by Figma plugin)

    Request body:
    {
        "status": "completed",
        "result_urls": ["https://..."]
    }
    """
    data = request.get_json()

    if not data:
        return jsonify({
            'error': {
                'code': 'INVALID_REQUEST',
                'message': 'Request body is required'
            }
        }), 400

    status = data.get('status')
    result_urls = data.get('result_urls', [])

    if status not in ['pending', 'processing', 'completed', 'failed']:
        return jsonify({
            'error': {
                'code': 'INVALID_STATUS',
                'message': 'Status must be: pending, processing, completed, or failed'
            }
        }), 400

    try:
        # Update job in Google Sheets
        sheets_client.update_fill_job(job_id, status, result_urls if result_urls else None)

        # Log status update
        current_user = get_jwt_identity()
        sheets_client.log_audit(
            actor=current_user,
            action='job.updated',
            target_id=job_id,
            metadata={'status': status, 'result_count': len(result_urls)}
        )

        return jsonify({
            'job_id': job_id,
            'status': status,
            'message': 'Job updated successfully'
        }), 200

    except Exception as e:
        print(f"Error updating job: {e}")
        return jsonify({
            'error': {
                'code': 'UPDATE_FAILED',
                'message': 'Failed to update job'
            }
        }), 500
