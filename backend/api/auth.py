"""
Authentication API endpoints
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
import bcrypt
from services.sheets import GoogleSheetsClient

bp = Blueprint('auth', __name__)
sheets_client = GoogleSheetsClient()


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

    # Get user from Google Sheets
    user = sheets_client.get_user_by_email(email)

    if not user:
        return jsonify({
            'error': {
                'code': 'INVALID_CREDENTIALS',
                'message': 'Invalid email or password'
            }
        }), 401

    # Verify password
    password_hash = user.get('password_hash')
    if not password_hash:
        return jsonify({
            'error': {
                'code': 'INVALID_CREDENTIALS',
                'message': 'Invalid email or password'
            }
        }), 401

    if not bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8')):
        return jsonify({
            'error': {
                'code': 'INVALID_CREDENTIALS',
                'message': 'Invalid email or password'
            }
        }), 401

    # Create JWT token
    access_token = create_access_token(identity=email)

    # Log successful login
    sheets_client.log_audit(
        actor=email,
        action='user.login',
        target_id=user['id'],
        metadata={'email': email}
    )

    return jsonify({
        'token': access_token,
        'user': {
            'id': user['id'],
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

    # Validate email format
    if '@' not in email or '.' not in email.split('@')[1]:
        return jsonify({
            'error': {
                'code': 'INVALID_EMAIL',
                'message': 'Invalid email format'
            }
        }), 400

    # Validate password length
    if len(password) < 8:
        return jsonify({
            'error': {
                'code': 'WEAK_PASSWORD',
                'message': 'Password must be at least 8 characters'
            }
        }), 400

    # Check if user already exists
    existing_user = sheets_client.get_user_by_email(email)
    if existing_user:
        return jsonify({
            'error': {
                'code': 'USER_EXISTS',
                'message': 'User with this email already exists'
            }
        }), 409

    # Hash password with bcrypt
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # Create user in Google Sheets
    try:
        user_id = sheets_client.create_user(email, password_hash)

        return jsonify({
            'message': 'User registered successfully',
            'user': {
                'id': user_id,
                'email': email
            }
        }), 201

    except Exception as e:
        return jsonify({
            'error': {
                'code': 'REGISTRATION_FAILED',
                'message': 'Failed to register user'
            }
        }), 500
