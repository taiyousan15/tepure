"""
Google Sheets service tests - Testing database operations
"""
import pytest
import json
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime
from services.sheets import GoogleSheetsClient


@pytest.fixture
def mock_sheets_service():
    """Mock Google Sheets service"""
    mock_service = MagicMock()
    mock_service.spreadsheets.return_value.values.return_value.get.return_value.execute.return_value = {
        'values': []
    }
    return mock_service


@pytest.fixture
def sheets_client(mock_sheets_service):
    """GoogleSheetsClient fixture with mocked service"""
    with patch('services.sheets.build') as mock_build, \
         patch('services.sheets.service_account.Credentials.from_service_account_info') as mock_creds:
        mock_build.return_value = mock_sheets_service
        mock_creds.return_value = MagicMock()

        client = GoogleSheetsClient()
        client.service = mock_sheets_service
        yield client


class TestGoogleSheetsClientInitialization:
    """Test GoogleSheetsClient initialization"""

    @patch('services.sheets.build')
    @patch('services.sheets.service_account.Credentials.from_service_account_info')
    @patch('services.sheets.base64.b64decode')
    @patch('services.sheets.json.loads')
    def test_initialize_service_success(self, mock_json_loads, mock_b64decode, mock_creds, mock_build):
        """Test successful service initialization"""
        mock_json_loads.return_value = {'type': 'service_account'}
        mock_b64decode.return_value = b'{"type": "service_account"}'
        mock_creds.return_value = MagicMock()
        mock_build.return_value = MagicMock()

        client = GoogleSheetsClient()

        assert client.service is not None
        mock_build.assert_called_once()

    @patch('services.sheets.os.getenv')
    def test_initialize_service_missing_credentials(self, mock_getenv):
        """Test initialization fails with missing credentials"""
        mock_getenv.return_value = None

        with pytest.raises(ValueError, match="GOOGLE_SERVICE_ACCOUNT_JSON"):
            GoogleSheetsClient()


class TestGetTemplates:
    """Test get_templates method"""

    def test_get_templates_success(self, sheets_client, mock_sheets_service):
        """Test getting templates successfully"""
        # Mock response data
        mock_sheets_service.spreadsheets().values().get().execute.return_value = {
            'values': [
                ['id', 'name', 'figma_file_id', 'figma_node_id', 'category', 'thumbnail_url', 'created_at'],
                ['tpl_1', 'Template 1', 'file_1', 'node_1', 'marketing', 'http://thumb1.png', '2025-10-16T00:00:00Z'],
                ['tpl_2', 'Template 2', 'file_2', 'node_2', 'social', 'http://thumb2.png', '2025-10-16T01:00:00Z']
            ]
        }

        templates = sheets_client.get_templates()

        assert len(templates) == 2
        assert templates[0]['id'] == 'tpl_1'
        assert templates[0]['name'] == 'Template 1'
        assert templates[1]['id'] == 'tpl_2'

    def test_get_templates_with_pagination(self, sheets_client, mock_sheets_service):
        """Test getting templates with limit and offset"""
        mock_sheets_service.spreadsheets().values().get().execute.return_value = {
            'values': [
                ['id', 'name', 'figma_file_id', 'figma_node_id', 'category', 'thumbnail_url', 'created_at'],
                ['tpl_1', 'Template 1', 'file_1', 'node_1', 'marketing', 'http://thumb1.png', '2025-10-16T00:00:00Z'],
                ['tpl_2', 'Template 2', 'file_2', 'node_2', 'social', 'http://thumb2.png', '2025-10-16T01:00:00Z'],
                ['tpl_3', 'Template 3', 'file_3', 'node_3', 'email', 'http://thumb3.png', '2025-10-16T02:00:00Z']
            ]
        }

        templates = sheets_client.get_templates(limit=1, offset=1)

        assert len(templates) == 1
        assert templates[0]['id'] == 'tpl_2'

    def test_get_templates_empty_sheet(self, sheets_client, mock_sheets_service):
        """Test getting templates from empty sheet"""
        mock_sheets_service.spreadsheets().values().get().execute.return_value = {
            'values': [['id', 'name', 'figma_file_id']]  # Only header
        }

        templates = sheets_client.get_templates()

        assert len(templates) == 0

    def test_get_templates_http_error(self, sheets_client, mock_sheets_service):
        """Test handling HTTP error when getting templates"""
        from googleapiclient.errors import HttpError

        mock_error = HttpError(resp=Mock(status=500), content=b'Error')
        mock_sheets_service.spreadsheets().values().get().execute.side_effect = mock_error

        templates = sheets_client.get_templates()

        assert templates == []


class TestGetTemplate:
    """Test get_template method"""

    def test_get_template_success(self, sheets_client, mock_sheets_service):
        """Test getting single template successfully"""
        mock_sheets_service.spreadsheets().values().get().execute.return_value = {
            'values': [
                ['id', 'name', 'figma_file_id', 'figma_node_id', 'category', 'thumbnail_url', 'created_at'],
                ['tpl_1', 'Template 1', 'file_1', 'node_1', 'marketing', 'http://thumb1.png', '2025-10-16T00:00:00Z']
            ]
        }

        template = sheets_client.get_template('tpl_1')

        assert template is not None
        assert template['id'] == 'tpl_1'
        assert template['name'] == 'Template 1'

    def test_get_template_not_found(self, sheets_client, mock_sheets_service):
        """Test getting non-existent template"""
        mock_sheets_service.spreadsheets().values().get().execute.return_value = {
            'values': [
                ['id', 'name', 'figma_file_id']
            ]
        }

        template = sheets_client.get_template('nonexistent')

        assert template is None

    def test_get_template_http_error(self, sheets_client, mock_sheets_service):
        """Test handling HTTP error when getting template"""
        from googleapiclient.errors import HttpError

        mock_error = HttpError(resp=Mock(status=500), content=b'Error')
        mock_sheets_service.spreadsheets().values().get().execute.side_effect = mock_error

        template = sheets_client.get_template('tpl_1')

        assert template is None


class TestCreateTemplate:
    """Test create_template method"""

    def test_create_template_success(self, sheets_client, mock_sheets_service):
        """Test creating template successfully"""
        mock_sheets_service.spreadsheets().values().append().execute.return_value = {}

        template_data = {
            'name': 'New Template',
            'figma_file_id': 'file_123',
            'figma_node_id': 'node_123',
            'category': 'marketing',
            'thumbnail_url': 'http://thumb.png'
        }

        template_id = sheets_client.create_template(template_data)

        assert template_id.startswith('tpl_')
        mock_sheets_service.spreadsheets().values().append.assert_called_once()

    def test_create_template_minimal_data(self, sheets_client, mock_sheets_service):
        """Test creating template with minimal data"""
        mock_sheets_service.spreadsheets().values().append().execute.return_value = {}

        template_data = {
            'name': 'Minimal Template'
        }

        template_id = sheets_client.create_template(template_data)

        assert template_id.startswith('tpl_')

    def test_create_template_http_error(self, sheets_client, mock_sheets_service):
        """Test handling HTTP error when creating template"""
        from googleapiclient.errors import HttpError

        mock_error = HttpError(resp=Mock(status=500), content=b'Error')
        mock_sheets_service.spreadsheets().values().append().execute.side_effect = mock_error

        with pytest.raises(HttpError):
            sheets_client.create_template({'name': 'Test'})


class TestGetTemplateFields:
    """Test get_template_fields method"""

    def test_get_template_fields_success(self, sheets_client, mock_sheets_service):
        """Test getting template fields successfully"""
        mock_sheets_service.spreadsheets().values().get().execute.return_value = {
            'values': [
                ['id', 'template_id', 'field_name', 'field_type', 'default_value', 'layer_name'],
                ['fld_1', 'tpl_1', 'title', 'text', 'Default Title', 'Title Layer'],
                ['fld_2', 'tpl_1', 'subtitle', 'text', 'Default Subtitle', 'Subtitle Layer']
            ]
        }

        fields = sheets_client.get_template_fields('tpl_1')

        assert len(fields) == 2
        assert fields[0]['field_name'] == 'title'
        assert fields[1]['field_name'] == 'subtitle'

    def test_get_template_fields_no_fields(self, sheets_client, mock_sheets_service):
        """Test getting template fields when none exist"""
        mock_sheets_service.spreadsheets().values().get().execute.return_value = {
            'values': [['id', 'template_id', 'field_name']]
        }

        fields = sheets_client.get_template_fields('tpl_1')

        assert len(fields) == 0


class TestCreateFillJob:
    """Test create_fill_job method"""

    def test_create_fill_job_success(self, sheets_client, mock_sheets_service):
        """Test creating fill job successfully"""
        mock_sheets_service.spreadsheets().values().append().execute.return_value = {}

        job_data = {
            'user_id': 'usr_123',
            'template_id': 'tpl_123',
            'input_data': {'title': 'Test Title'}
        }

        job_id = sheets_client.create_fill_job(job_data)

        assert job_id.startswith('job_')
        mock_sheets_service.spreadsheets().values().append.assert_called_once()

    def test_create_fill_job_http_error(self, sheets_client, mock_sheets_service):
        """Test handling HTTP error when creating job"""
        from googleapiclient.errors import HttpError

        mock_error = HttpError(resp=Mock(status=500), content=b'Error')
        mock_sheets_service.spreadsheets().values().append().execute.side_effect = mock_error

        with pytest.raises(HttpError):
            sheets_client.create_fill_job({'user_id': 'usr_1', 'template_id': 'tpl_1'})


class TestUpdateFillJob:
    """Test update_fill_job method"""

    def test_update_fill_job_success(self, sheets_client, mock_sheets_service):
        """Test updating fill job successfully"""
        # Mock get to find job
        mock_sheets_service.spreadsheets().values().get().execute.return_value = {
            'values': [
                ['job_id', 'user_id', 'template_id', 'status', 'input_data', 'result_urls', 'created_at', 'updated_at'],
                ['job_123', 'usr_1', 'tpl_1', 'pending', '{}', '', '2025-10-16T00:00:00Z', '2025-10-16T00:00:00Z']
            ]
        }

        # Mock update
        mock_sheets_service.spreadsheets().values().update().execute.return_value = {}

        sheets_client.update_fill_job('job_123', 'completed', ['http://result.png'])

        mock_sheets_service.spreadsheets().values().update.assert_called_once()

    def test_update_fill_job_not_found(self, sheets_client, mock_sheets_service):
        """Test updating non-existent job"""
        mock_sheets_service.spreadsheets().values().get().execute.return_value = {
            'values': [['job_id', 'user_id', 'template_id', 'status']]
        }

        # Should not raise error, just log warning
        sheets_client.update_fill_job('nonexistent', 'completed')


class TestGetFillJobs:
    """Test get_fill_jobs method"""

    def test_get_fill_jobs_success(self, sheets_client, mock_sheets_service):
        """Test getting fill jobs successfully"""
        mock_sheets_service.spreadsheets().values().get().execute.return_value = {
            'values': [
                ['job_id', 'user_id', 'template_id', 'status', 'input_data', 'result_urls', 'created_at', 'updated_at'],
                ['job_1', 'usr_1', 'tpl_1', 'completed', '{"title": "Test"}', '[]', '2025-10-16T00:00:00Z', '2025-10-16T01:00:00Z'],
                ['job_2', 'usr_1', 'tpl_2', 'pending', '{"title": "Test2"}', '[]', '2025-10-16T02:00:00Z', '2025-10-16T02:00:00Z']
            ]
        }

        jobs = sheets_client.get_fill_jobs('usr_1')

        assert len(jobs) == 2
        assert jobs[0]['job_id'] in ['job_1', 'job_2']

    def test_get_fill_jobs_with_status_filter(self, sheets_client, mock_sheets_service):
        """Test getting fill jobs with status filter"""
        mock_sheets_service.spreadsheets().values().get().execute.return_value = {
            'values': [
                ['job_id', 'user_id', 'template_id', 'status', 'input_data', 'result_urls', 'created_at', 'updated_at'],
                ['job_1', 'usr_1', 'tpl_1', 'completed', '{}', '[]', '2025-10-16T00:00:00Z', '2025-10-16T01:00:00Z'],
                ['job_2', 'usr_1', 'tpl_2', 'pending', '{}', '[]', '2025-10-16T02:00:00Z', '2025-10-16T02:00:00Z']
            ]
        }

        jobs = sheets_client.get_fill_jobs('usr_1', status_filter='pending')

        assert len(jobs) == 1
        assert jobs[0]['status'] == 'pending'


class TestUserOperations:
    """Test user-related operations"""

    def test_get_user_by_email_success(self, sheets_client, mock_sheets_service):
        """Test getting user by email successfully"""
        mock_sheets_service.spreadsheets().values().get().execute.return_value = {
            'values': [
                ['id', 'email', 'password_hash', 'created_at'],
                ['usr_1', 'test@example.com', 'hash123', '2025-10-16T00:00:00Z']
            ]
        }

        user = sheets_client.get_user_by_email('test@example.com')

        assert user is not None
        assert user['id'] == 'usr_1'
        assert user['email'] == 'test@example.com'

    def test_get_user_by_email_not_found(self, sheets_client, mock_sheets_service):
        """Test getting non-existent user"""
        mock_sheets_service.spreadsheets().values().get().execute.return_value = {
            'values': [['id', 'email', 'password_hash']]
        }

        user = sheets_client.get_user_by_email('nonexistent@example.com')

        assert user is None

    def test_create_user_success(self, sheets_client, mock_sheets_service):
        """Test creating user successfully"""
        mock_sheets_service.spreadsheets().values().append().execute.return_value = {}

        user_id = sheets_client.create_user('newuser@example.com', 'hashed_password')

        assert user_id.startswith('usr_')
        assert mock_sheets_service.spreadsheets().values().append.call_count >= 1


class TestAuditLogging:
    """Test audit logging"""

    def test_log_audit_success(self, sheets_client, mock_sheets_service):
        """Test logging audit entry successfully"""
        mock_sheets_service.spreadsheets().values().append().execute.return_value = {}

        sheets_client.log_audit(
            actor='test@example.com',
            action='template.created',
            target_id='tpl_123',
            metadata={'name': 'Test Template'}
        )

        mock_sheets_service.spreadsheets().values().append.assert_called_once()

    def test_log_audit_http_error(self, sheets_client, mock_sheets_service):
        """Test handling HTTP error when logging audit"""
        from googleapiclient.errors import HttpError

        mock_error = HttpError(resp=Mock(status=500), content=b'Error')
        mock_sheets_service.spreadsheets().values().append().execute.side_effect = mock_error

        # Should not raise error, just log warning
        sheets_client.log_audit('test@example.com', 'action', 'target', {})
