"""
Templates API endpoints
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

bp = Blueprint('templates', __name__)


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

    # TODO: Implement actual database query
    # Mock response
    templates = [
        {
            'id': 'tpl_001',
            'name': 'LP-ヒーロー左画像',
            'category': 'LP',
            'preview_url': 'https://example.com/preview1.png',
            'created_at': '2025-10-16T00:00:00Z'
        },
        {
            'id': 'tpl_002',
            'name': 'LP-ヒーロー右画像',
            'category': 'LP',
            'preview_url': 'https://example.com/preview2.png',
            'created_at': '2025-10-16T00:00:00Z'
        }
    ]

    return jsonify({
        'templates': templates,
        'total': len(templates),
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
    # TODO: Implement actual database query
    # Mock response
    template = {
        'id': template_id,
        'name': 'LP-ヒーロー左画像',
        'category': 'LP',
        'preview_url': 'https://example.com/preview1.png',
        'figma_file_key': 'XXXXX',
        'fields': [
            {
                'node_id': 'HEAD_TITLE',
                'type': 'TEXT',
                'max_chars': 36,
                'required': True
            }
        ]
    }

    return jsonify(template), 200


@bp.route('', methods=['POST'])
@jwt_required()
def create_template():
    """
    Create a new template (admin only)

    Request body:
    {
        "name": "LP-ヒーロー左画像",
        "category": "LP",
        "figma_file_key": "XXXXX",
        "preview_url": "https://...",
        "fields": [...]
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

    # TODO: Implement actual template creation
    # For now, return mock response

    return jsonify({
        'id': 'tpl_new',
        'message': 'Template created successfully'
    }), 201


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
