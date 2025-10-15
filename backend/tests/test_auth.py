"""
Authentication API tests
"""
import pytest
import json
from unittest.mock import patch, MagicMock


class TestAuthEndpoints:
    """Test authentication endpoints"""

    @patch('api.auth.sheets_client')
    def test_login_success(self, mock_sheets, client):
        """Test successful login"""
        # Mock user data
        mock_sheets.get_user_by_email.return_value = {
            'id': 'usr_123',
            'email': 'test@example.com',
            'password_hash': '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzNW6s6rqO',  # "password123"
            'created_at': '2025-10-16T00:00:00Z'
        }
        mock_sheets.log_audit.return_value = None

        # Make request
        response = client.post('/api/v1/auth/login', json={
            'email': 'test@example.com',
            'password': 'password123'
        })

        # Assert response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'token' in data
        assert data['user']['email'] == 'test@example.com'
        assert data['user']['id'] == 'usr_123'

    @patch('api.auth.sheets_client')
    def test_login_invalid_credentials(self, mock_sheets, client):
        """Test login with invalid credentials"""
        # Mock user not found
        mock_sheets.get_user_by_email.return_value = None

        # Make request
        response = client.post('/api/v1/auth/login', json={
            'email': 'nonexistent@example.com',
            'password': 'wrongpassword'
        })

        # Assert response
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['error']['code'] == 'INVALID_CREDENTIALS'

    @patch('api.auth.sheets_client')
    def test_login_missing_fields(self, mock_sheets, client):
        """Test login with missing fields"""
        # Make request without password
        response = client.post('/api/v1/auth/login', json={
            'email': 'test@example.com'
        })

        # Assert response
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error']['code'] == 'MISSING_FIELDS'

    @patch('api.auth.sheets_client')
    def test_register_success(self, mock_sheets, client):
        """Test successful user registration"""
        # Mock user does not exist
        mock_sheets.get_user_by_email.return_value = None
        mock_sheets.create_user.return_value = 'usr_new123'

        # Make request
        response = client.post('/api/v1/auth/register', json={
            'email': 'newuser@example.com',
            'password': 'password123'
        })

        # Assert response
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['message'] == 'User registered successfully'
        assert data['user']['id'] == 'usr_new123'
        assert data['user']['email'] == 'newuser@example.com'

    @patch('api.auth.sheets_client')
    def test_register_user_exists(self, mock_sheets, client):
        """Test registration when user already exists"""
        # Mock user exists
        mock_sheets.get_user_by_email.return_value = {
            'id': 'usr_existing',
            'email': 'existing@example.com'
        }

        # Make request
        response = client.post('/api/v1/auth/register', json={
            'email': 'existing@example.com',
            'password': 'password123'
        })

        # Assert response
        assert response.status_code == 409
        data = json.loads(response.data)
        assert data['error']['code'] == 'USER_EXISTS'

    @patch('api.auth.sheets_client')
    def test_register_weak_password(self, mock_sheets, client):
        """Test registration with weak password"""
        # Mock user does not exist
        mock_sheets.get_user_by_email.return_value = None

        # Make request with short password
        response = client.post('/api/v1/auth/register', json={
            'email': 'newuser@example.com',
            'password': 'short'
        })

        # Assert response
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error']['code'] == 'WEAK_PASSWORD'

    @patch('api.auth.sheets_client')
    def test_register_invalid_email(self, mock_sheets, client):
        """Test registration with invalid email"""
        # Mock user does not exist
        mock_sheets.get_user_by_email.return_value = None

        # Make request with invalid email
        response = client.post('/api/v1/auth/register', json={
            'email': 'invalid-email',
            'password': 'password123'
        })

        # Assert response
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error']['code'] == 'INVALID_EMAIL'
