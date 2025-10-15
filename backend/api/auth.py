"""
Authentication API endpoints
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
import bcrypt

bp = Blueprint('auth', __name__)


@bp.route('/login', methods=['POST'])
def login():
    """
    User login endpoint

    Request body:
    {
        "email": "user@example.com",
        "password": "password123"
    }

    Response:
    {
        "token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
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

    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({
            'error': {
                'code': 'MISSING_FIELDS',
                'message': 'Email and password are required'
            }
        }), 400

    # TODO: Implement actual user authentication with database
    # For now, return a mock token

    # Create JWT token
    access_token = create_access_token(identity=email)

    return jsonify({
        'token': access_token,
        'user': {
            'email': email
        }
    }), 200


@bp.route('/register', methods=['POST'])
def register():
    """
    User registration endpoint

    Request body:
    {
        "email": "user@example.com",
        "password": "password123"
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

    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({
            'error': {
                'code': 'MISSING_FIELDS',
                'message': 'Email and password are required'
            }
        }), 400

    # TODO: Implement actual user registration with database
    # Hash password with bcrypt
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    return jsonify({
        'message': 'User registered successfully',
        'user': {
            'email': email
        }
    }), 201
