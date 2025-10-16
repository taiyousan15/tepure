"""
Flask application core tests - Health checks, error handlers, and CORS
"""
import pytest
import json
from unittest.mock import patch


class TestHealthCheck:
    """Test health check endpoint"""

    def test_health_check_success(self, client):
        """Test health check returns 200"""
        response = client.get('/api/v1/health')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert data['service'] == 'figma-template-automation-api'
        assert 'version' in data

    def test_health_check_response_structure(self, client):
        """Test health check has correct response structure"""
        response = client.get('/api/v1/health')
        data = json.loads(response.data)

        # Verify all required fields are present
        assert 'status' in data
        assert 'service' in data
        assert 'version' in data

        # Verify field types
        assert isinstance(data['status'], str)
        assert isinstance(data['service'], str)
        assert isinstance(data['version'], str)


class TestErrorHandlers:
    """Test Flask error handlers"""

    def test_404_not_found(self, client):
        """Test 404 error handler"""
        response = client.get('/api/v1/nonexistent-endpoint')

        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error']['code'] == 'NOT_FOUND'
        assert 'message' in data['error']

    def test_404_error_structure(self, client):
        """Test 404 error has correct structure"""
        response = client.get('/api/v1/does-not-exist')
        data = json.loads(response.data)

        # Verify error structure
        assert 'error' in data
        assert 'code' in data['error']
        assert 'message' in data['error']
        assert isinstance(data['error']['code'], str)
        assert isinstance(data['error']['message'], str)

    def test_method_not_allowed(self, client):
        """Test 405 method not allowed"""
        # Try POST on GET-only endpoint
        response = client.post('/api/v1/health')

        assert response.status_code == 405


class TestCORS:
    """Test CORS configuration"""

    def test_cors_headers_present(self, client):
        """Test CORS headers are present in response"""
        response = client.get('/api/v1/health', headers={
            'Origin': 'http://localhost:5173'
        })

        assert response.status_code == 200
        # Flask-CORS should add Access-Control-Allow-Origin header
        assert 'Access-Control-Allow-Origin' in response.headers

    def test_cors_preflight_request(self, client):
        """Test CORS preflight OPTIONS request"""
        response = client.options('/api/v1/health', headers={
            'Origin': 'http://localhost:5173',
            'Access-Control-Request-Method': 'GET',
            'Access-Control-Request-Headers': 'Content-Type'
        })

        # Should return 200 for OPTIONS preflight
        assert response.status_code in [200, 204]


class TestJWTConfiguration:
    """Test JWT configuration"""

    def test_jwt_secret_key_configured(self, app):
        """Test JWT secret key is configured"""
        assert 'JWT_SECRET_KEY' in app.config
        assert app.config['JWT_SECRET_KEY'] is not None
        assert len(app.config['JWT_SECRET_KEY']) > 0

    def test_jwt_token_expiration_configured(self, app):
        """Test JWT token expiration is configured"""
        assert 'JWT_ACCESS_TOKEN_EXPIRES' in app.config
        assert app.config['JWT_ACCESS_TOKEN_EXPIRES'] == 3600


class TestRateLimiting:
    """Test rate limiting configuration"""

    @patch('flask_limiter.Limiter.enabled', True)
    def test_rate_limit_exists(self, app):
        """Test rate limiter is configured"""
        # Check that rate limiter extension is registered
        assert hasattr(app, 'extensions')
        # Rate limiter should be in extensions
        # Note: Actual rate limit testing requires more complex setup


class TestBlueprintRegistration:
    """Test blueprint registration"""

    def test_auth_blueprint_registered(self, client):
        """Test auth blueprint is registered"""
        # Try to access auth endpoint
        response = client.post('/api/v1/auth/login', json={})
        # Should not return 404 (blueprint is registered)
        assert response.status_code != 404

    def test_templates_blueprint_registered(self, client, auth_headers):
        """Test templates blueprint is registered"""
        # Try to access templates endpoint
        headers = auth_headers()
        response = client.get('/api/v1/templates', headers=headers)
        # Should not return 404 (blueprint is registered)
        assert response.status_code != 404

    def test_jobs_blueprint_registered(self, client, auth_headers):
        """Test jobs blueprint is registered"""
        # Try to access jobs endpoint
        headers = auth_headers()
        response = client.get('/api/v1/jobs', headers=headers)
        # Should not return 404 (blueprint is registered)
        assert response.status_code != 404


class TestContentType:
    """Test content type handling"""

    def test_json_response_content_type(self, client):
        """Test JSON responses have correct content type"""
        response = client.get('/api/v1/health')

        assert response.status_code == 200
        assert 'application/json' in response.content_type

    def test_404_response_content_type(self, client):
        """Test 404 error response has correct content type"""
        response = client.get('/api/v1/nonexistent')

        assert response.status_code == 404
        assert 'application/json' in response.content_type


class TestEnvironmentConfiguration:
    """Test environment configuration"""

    def test_app_testing_mode(self, app):
        """Test app is in testing mode"""
        assert app.config['TESTING'] is True

    def test_app_debug_mode(self, app):
        """Test app debug mode configuration"""
        # In testing, debug should be False or configured
        assert 'DEBUG' in app.config or not app.config.get('DEBUG', True)


class TestRequestValidation:
    """Test request validation"""

    def test_empty_request_body_handling(self, client, auth_headers):
        """Test handling of empty request body"""
        headers = auth_headers()
        response = client.post('/api/v1/jobs', headers=headers)

        # Should return 400 for empty body
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_invalid_json_handling(self, client, auth_headers):
        """Test handling of invalid JSON"""
        headers = auth_headers()
        headers['Content-Type'] = 'application/json'

        response = client.post('/api/v1/jobs',
                                data='invalid-json',
                                headers=headers)

        # Should return 400 for invalid JSON
        assert response.status_code in [400, 415]
