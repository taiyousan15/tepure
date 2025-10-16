"""
Unit tests for authentication module
"""
import pytest
from app.auth import (
    hash_password,
    verify_password,
    create_access_token_for_user,
    create_refresh_token_for_user,
    mask_pii
)


def test_hash_password():
    """Test password hashing"""
    password = "test_password_123"
    hashed = hash_password(password)

    assert hashed is not None
    assert hashed != password
    assert len(hashed) > 20


def test_hash_password_too_short():
    """Test password too short raises error"""
    with pytest.raises(ValueError):
        hash_password("short")


def test_verify_password_success():
    """Test password verification success"""
    password = "test_password_123"
    hashed = hash_password(password)

    assert verify_password(password, hashed) is True


def test_verify_password_failure():
    """Test password verification failure"""
    password = "test_password_123"
    hashed = hash_password(password)

    assert verify_password("wrong_password", hashed) is False


def test_create_access_token():
    """Test access token creation"""
    token = create_access_token_for_user("user_123", "user")

    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 50


def test_create_refresh_token():
    """Test refresh token creation"""
    token = create_refresh_token_for_user("user_123")

    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 50


def test_mask_pii():
    """Test PII masking"""
    data = {
        'email': 'user@example.com',
        'password': 'secret123',
        'name': 'John Doe'
    }

    masked = mask_pii(data)

    assert 'us***om' in masked['email']
    assert '***' in masked['password']
    assert masked['name'] == 'John Doe'  # Non-PII field unchanged
