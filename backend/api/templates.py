"""
Templates API endpoints
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.sheets import GoogleSheetsClient

bp = Blueprint('templates', __name__)
sheets_client = GoogleSheetsClient()


@bp.route('', methods=['GET'])
@jwt_required()
def list_templates():
    """
    List all templates

    Query parameters:
    - limit: Maximum number of templates to return (default: 20)
    - offset: Number of templates to skip (default: 0)
    - category: Filter by category

    Response:
    {
        "templates": [
            {
                "id": "tpl_001",
                "name": "LP-ヒーロー左画像",
                "category": "LP",
                "preview_url": "https://...",
                "created_at": "2025-10-16T00:00:00Z"
            }
        ],
        "total": 30,
        "limit": 20,
        "offset": 0
    }
    """
    limit = request.args.get('limit', 20, type=int)
    offset = request.args.get('offset', 0, type=int)
    category = request.args.get('category', type=str)

    # Get templates from Google Sheets
    templates = sheets_client.get_templates(limit=limit, offset=offset)

    # Filter by category if specified
    if category:
        templates = [t for t in templates if t.get('category') == category]

    # Map to response format
    response_templates = []
    for t in templates:
        response_templates.append({
            'id': t['id'],
            'name': t['name'],
            'category': t.get('category', 'uncategorized'),
            'preview_url': t.get('thumbnail_url', ''),
            'created_at': t.get('created_at', '')
        })

    return jsonify({
        'templates': response_templates,
        'total': len(response_templates),
        'limit': limit,
        'offset': offset
    }), 200


@bp.route('/<template_id>', methods=['GET'])
@jwt_required()
def get_template(template_id):
    """
    Get template details

    Response:
    {
        "id": "tpl_001",
        "name": "LP-ヒーロー左画像",
        "category": "LP",
        "preview_url": "https://...",
        "figma_file_key": "XXXXX",
        "fields": [
            {
                "node_id": "HEAD_TITLE",
                "type": "TEXT",
                "max_chars": 36,
                "required": true
            }
        ]
    }
    """
    # Get template from Google Sheets
    template = sheets_client.get_template(template_id)

    if not template:
        return jsonify({
            'error': {
                'code': 'NOT_FOUND',
                'message': 'Template not found'
            }
        }), 404

    # Get template fields
    fields = sheets_client.get_template_fields(template_id)

    # Map to response format
    response = {
        'id': template['id'],
        'name': template['name'],
        'category': template.get('category', 'uncategorized'),
        'preview_url': template.get('thumbnail_url', ''),
        'figma_file_key': template.get('figma_file_id', ''),
        'figma_node_id': template.get('figma_node_id', ''),
        'fields': [
            {
                'id': f['id'],
                'node_id': f.get('field_name', ''),
                'type': f.get('field_type', 'text').upper(),
                'layer_name': f.get('layer_name', ''),
                'default_value': f.get('default_value', ''),
                'required': True  # Default to true for now
            }
            for f in fields
        ]
    }

    return jsonify(response), 200


@bp.route('', methods=['POST'])
@jwt_required()
def create_template():
    """
    Create a new template (admin only)

    Request body:
    {
        "name": "LP-ヒーロー左画像",
        "category": "LP",
        "figma_file_id": "XXXXX",
        "figma_node_id": "123:456",
        "thumbnail_url": "https://...",
        "fields": [
            {
                "field_name": "HEAD_TITLE",
                "field_type": "text",
                "default_value": "",
                "layer_name": "ヘッドライン"
            }
        ]
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
    required_fields = ['name', 'figma_file_id']
    for field in required_fields:
        if not data.get(field):
            return jsonify({
                'error': {
                    'code': 'MISSING_FIELD',
                    'message': f'Missing required field: {field}'
                }
            }), 400

    # Create template in Google Sheets
    try:
        template_data = {
            'name': data['name'],
            'figma_file_id': data['figma_file_id'],
            'figma_node_id': data.get('figma_node_id', ''),
            'category': data.get('category', 'uncategorized'),
            'thumbnail_url': data.get('thumbnail_url', '')
        }

        template_id = sheets_client.create_template(template_data)

        # Create template fields if provided
        if 'fields' in data and isinstance(data['fields'], list):
            # TODO: Implement field creation
            pass

        # Log template creation
        current_user = get_jwt_identity()
        sheets_client.log_audit(
            actor=current_user,
            action='template.created',
            target_id=template_id,
            metadata={'name': data['name'], 'category': data.get('category', 'uncategorized')}
        )

        return jsonify({
            'id': template_id,
            'message': 'Template created successfully'
        }), 201

    except Exception as e:
        return jsonify({
            'error': {
                'code': 'CREATION_FAILED',
                'message': 'Failed to create template'
            }
        }), 500


@bp.route('/<template_id>/fields', methods=['GET'])
@jwt_required()
def get_template_fields(template_id):
    """
    Get template fields

    Response:
    {
        "fields": [
            {
                "node_id": "HEAD_TITLE",
                "type": "TEXT",
                "max_chars": 36,
                "required": true,
                "allowed_sets": ["JP", "EN", "MIX"]
            }
        ]
    }
    """
    # TODO: Implement actual database query
    fields = [
        {
            'node_id': 'HEAD_TITLE',
            'type': 'TEXT',
            'max_chars': 36,
            'required': True,
            'allowed_sets': ['JP', 'EN', 'MIX']
        }
    ]

    return jsonify({'fields': fields}), 200
