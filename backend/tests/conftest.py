"""
Pytest configuration and fixtures
"""
import pytest
import os
from app import app as flask_app


@pytest.fixture
def app():
    """Flask application fixture"""
    flask_app.config.update({
        'TESTING': True,
        'JWT_SECRET_KEY': 'test-secret-key',
    })

    # Mock environment variables for testing
    os.environ['GOOGLE_SHEETS_ID'] = 'test-sheet-id'
    os.environ['GOOGLE_SERVICE_ACCOUNT_JSON'] = 'test-credentials'

    yield flask_app


@pytest.fixture
def client(app):
    """Flask test client fixture"""
    return app.test_client()


@pytest.fixture
def auth_headers(client):
    """
    Fixture that provides authentication headers
    Returns a function that generates headers with a valid JWT token
    """
    def _get_headers(email='test@example.com'):
        # Register and login to get a token
        from flask_jwt_extended import create_access_token

        # Create token directly (bypassing actual login)
        with client.application.app_context():
            token = create_access_token(identity=email)

        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

    return _get_headers
