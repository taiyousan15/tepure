"""
Pytest configuration and fixtures
"""
import pytest
import os
from unittest.mock import MagicMock, patch
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


@pytest.fixture
def mock_google_sheets():
    """Mock Google Sheets API service"""
    with patch('services.sheets.build') as mock_build, \
         patch('services.sheets.service_account.Credentials.from_service_account_info') as mock_creds:
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_creds.return_value = MagicMock()

        yield mock_service


@pytest.fixture
def sample_template():
    """Sample template data for testing"""
    return {
        'id': 'tpl_test123',
        'name': 'Test Template',
        'figma_file_id': 'figma_file_123',
        'figma_node_id': 'figma_node_123',
        'category': 'marketing',
        'thumbnail_url': 'https://example.com/thumbnail.png',
        'created_at': '2025-10-16T00:00:00Z'
    }


@pytest.fixture
def sample_user():
    """Sample user data for testing"""
    return {
        'id': 'usr_test123',
        'email': 'test@example.com',
        'password_hash': '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzNW6s6rqO',  # "password123"
        'created_at': '2025-10-16T00:00:00Z'
    }


@pytest.fixture
def sample_job():
    """Sample fill job data for testing"""
    return {
        'job_id': 'job_test123',
        'user_id': 'usr_test123',
        'template_id': 'tpl_test123',
        'status': 'pending',
        'input_data': {
            'HEAD_TITLE': '春の大セール開催中',
            'SUB_TITLE': '全商品30%OFF'
        },
        'result_urls': [],
        'created_at': '2025-10-16T00:00:00Z',
        'updated_at': '2025-10-16T00:00:00Z'
    }


@pytest.fixture
def sample_template_fields():
    """Sample template fields data for testing"""
    return [
        {
            'id': 'fld_1',
            'template_id': 'tpl_test123',
            'field_name': 'HEAD_TITLE',
            'field_type': 'text',
            'default_value': 'Default Title',
            'layer_name': 'Title Layer'
        },
        {
            'id': 'fld_2',
            'template_id': 'tpl_test123',
            'field_name': 'SUB_TITLE',
            'field_type': 'text',
            'default_value': 'Default Subtitle',
            'layer_name': 'Subtitle Layer'
        }
    ]
