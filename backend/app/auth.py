"""
Authentication and authorization utilities with role-based access control
"""
import os
import bcrypt
import structlog
from datetime import timedelta
from functools import wraps
from typing import Tuple, Optional
from flask import request, jsonify
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    verify_jwt_in_request,
    get_jwt_identity,
    get_jwt
)

logger = structlog.get_logger()


# ========== Password Hashing (BCrypt) ==========

def hash_password(password: str) -> str:
    """
    Hash a password using BCrypt

    Args:
        password: Plain text password

    Returns:
        BCrypt password hash
    """
    if not password or len(password) < 8:
        raise ValueError("Password must be at least 8 characters")

    salt = bcrypt.gensalt(rounds=12)
    password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
    return password_hash.decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify a password against a hash

    Args:
        password: Plain text password
        password_hash: BCrypt hash

    Returns:
        True if password matches, False otherwise
    """
    try:
        return bcrypt.checkpw(
            password.encode('utf-8'),
            password_hash.encode('utf-8')
        )
    except Exception as e:
        logger.error("password_verification_failed", error=str(e))
        return False


# ========== JWT Token Creation ==========

def create_access_token_for_user(user_id: str, role: str = 'user') -> str:
    """
    Create JWT access token

    Args:
        user_id: User ID
        role: User role (user or admin)

    Returns:
        JWT access token (15 minutes expiry)
    """
    additional_claims = {'role': role}
    expires_delta = timedelta(minutes=15)

    token = create_access_token(
        identity=user_id,
        additional_claims=additional_claims,
        expires_delta=expires_delta
    )

    logger.info("access_token_created", user_id=user_id, role=role)
    return token


def create_refresh_token_for_user(user_id: str) -> str:
    """
    Create JWT refresh token

    Args:
        user_id: User ID

    Returns:
        JWT refresh token (7 days expiry)
    """
    expires_delta = timedelta(days=7)

    token = create_refresh_token(
        identity=user_id,
        expires_delta=expires_delta
    )

    logger.info("refresh_token_created", user_id=user_id)
    return token


# ========== Authentication Decorators ==========

def require_auth(fn):
    """
    Decorator to require authentication for a route

    Usage:
        @app.route('/protected')
        @require_auth
        def protected():
            return {'message': 'Authenticated'}
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            jwt_data = get_jwt()

            logger.info(
                "authenticated_request",
                user_id=user_id,
                role=jwt_data.get('role'),
                path=request.path
            )

            return fn(*args, **kwargs)

        except Exception as e:
            logger.warning("authentication_failed", error=str(e), path=request.path)
            return jsonify({
                'code': 'UNAUTHORIZED',
                'message': 'Authentication required'
            }), 401

    return wrapper


def require_admin(fn):
    """
    Decorator to require admin role for a route

    Usage:
        @app.route('/admin')
        @require_admin
        def admin_only():
            return {'message': 'Admin access granted'}
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            jwt_data = get_jwt()
            role = jwt_data.get('role', 'user')

            if role != 'admin':
                logger.warning(
                    "authorization_failed",
                    user_id=user_id,
                    role=role,
                    path=request.path
                )
                return jsonify({
                    'code': 'FORBIDDEN',
                    'message': 'Admin privileges required'
                }), 403

            logger.info(
                "admin_request",
                user_id=user_id,
                path=request.path
            )

            return fn(*args, **kwargs)

        except Exception as e:
            logger.warning("authorization_failed", error=str(e), path=request.path)
            return jsonify({
                'code': 'UNAUTHORIZED',
                'message': 'Authentication required'
            }), 401

    return wrapper


# ========== Helper Functions ==========

def get_current_user_id() -> Optional[str]:
    """
    Get current authenticated user ID from JWT

    Returns:
        User ID or None if not authenticated
    """
    try:
        verify_jwt_in_request(optional=True)
        return get_jwt_identity()
    except Exception:
        return None


def get_current_user_role() -> str:
    """
    Get current authenticated user role from JWT

    Returns:
        User role ('user' or 'admin')
    """
    try:
        verify_jwt_in_request(optional=True)
        jwt_data = get_jwt()
        return jwt_data.get('role', 'user')
    except Exception:
        return 'user'


def mask_pii(data: dict) -> dict:
    """
    Mask personally identifiable information in logs

    Args:
        data: Dictionary containing potential PII

    Returns:
        Dictionary with PII masked
    """
    masked = data.copy()
    pii_fields = ['email', 'password', 'token', 'api_key', 'secret']

    for field in pii_fields:
        if field in masked:
            value = str(masked[field])
            if len(value) > 4:
                masked[field] = f"{value[:2]}***{value[-2:]}"
            else:
                masked[field] = "***"

    return masked
