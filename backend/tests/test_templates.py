"""
Templates API tests
"""
import pytest
import json
from unittest.mock import patch, MagicMock


class TestTemplatesEndpoints:
    """Test templates endpoints"""

    @patch('api.templates.sheets_client')
    def test_list_templates(self, mock_sheets, client, auth_headers):
        """Test listing templates"""
        # Mock templates data
        mock_sheets.get_templates.return_value = [
            {
                'id': 'tpl_001',
                'name': 'LP-ヒーロー左画像',
                'figma_file_id': 'file123',
                'figma_node_id': 'node123',
                'category': 'LP',
                'thumbnail_url': 'https://example.com/thumb1.png',
                'created_at': '2025-10-16T00:00:00Z'
            },
            {
                'id': 'tpl_002',
                'name': 'LP-ヒーロー右画像',
                'figma_file_id': 'file456',
                'figma_node_id': 'node456',
                'category': 'LP',
                'thumbnail_url': 'https://example.com/thumb2.png',
                'created_at': '2025-10-16T00:00:00Z'
            }
        ]

        # Make request
        response = client.get('/api/v1/templates', headers=auth_headers())

        # Assert response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['templates']) == 2
        assert data['templates'][0]['id'] == 'tpl_001'
        assert data['templates'][0]['name'] == 'LP-ヒーロー左画像'

    @patch('api.templates.sheets_client')
    def test_list_templates_with_category_filter(self, mock_sheets, client, auth_headers):
        """Test listing templates with category filter"""
        # Mock templates data
        mock_sheets.get_templates.return_value = [
            {
                'id': 'tpl_001',
                'name': 'LP-ヒーロー左画像',
                'figma_file_id': 'file123',
                'category': 'LP',
                'thumbnail_url': 'https://example.com/thumb1.png',
                'created_at': '2025-10-16T00:00:00Z'
            },
            {
                'id': 'tpl_003',
                'name': 'バナー広告',
                'figma_file_id': 'file789',
                'category': 'Banner',
                'thumbnail_url': 'https://example.com/thumb3.png',
                'created_at': '2025-10-16T00:00:00Z'
            }
        ]

        # Make request with category filter
        response = client.get('/api/v1/templates?category=LP', headers=auth_headers())

        # Assert response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['templates']) == 1
        assert data['templates'][0]['category'] == 'LP'

    @patch('api.templates.sheets_client')
    def test_get_template(self, mock_sheets, client, auth_headers):
        """Test getting a single template"""
        # Mock template data
        mock_sheets.get_template.return_value = {
            'id': 'tpl_001',
            'name': 'LP-ヒーロー左画像',
            'figma_file_id': 'file123',
            'figma_node_id': 'node123',
            'category': 'LP',
            'thumbnail_url': 'https://example.com/thumb1.png',
            'created_at': '2025-10-16T00:00:00Z'
        }

        mock_sheets.get_template_fields.return_value = [
            {
                'id': 'field_001',
                'template_id': 'tpl_001',
                'field_name': 'HEAD_TITLE',
                'field_type': 'text',
                'default_value': '',
                'layer_name': 'ヘッドライン'
            }
        ]

        # Make request
        response = client.get('/api/v1/templates/tpl_001', headers=auth_headers())

        # Assert response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['id'] == 'tpl_001'
        assert data['name'] == 'LP-ヒーロー左画像'
        assert len(data['fields']) == 1
        assert data['fields'][0]['node_id'] == 'HEAD_TITLE'

    @patch('api.templates.sheets_client')
    def test_get_template_not_found(self, mock_sheets, client, auth_headers):
        """Test getting a non-existent template"""
        # Mock template not found
        mock_sheets.get_template.return_value = None

        # Make request
        response = client.get('/api/v1/templates/nonexistent', headers=auth_headers())

        # Assert response
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error']['code'] == 'NOT_FOUND'

    def test_list_templates_unauthorized(self, client):
        """Test listing templates without authentication"""
        # Make request without auth headers
        response = client.get('/api/v1/templates')

        # Assert response
        assert response.status_code == 401

    def test_get_template_unauthorized(self, client):
        """Test getting template without authentication"""
        # Make request without auth headers
        response = client.get('/api/v1/templates/tpl_001')

        # Assert response
        assert response.status_code == 401
