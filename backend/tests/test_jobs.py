"""
Jobs API endpoint tests - Template fill job management
"""
import pytest
import json
from unittest.mock import patch, MagicMock


@pytest.fixture
def mock_sheets_client():
    """Mock GoogleSheetsClient"""
    with patch('api.jobs.sheets_client') as mock:
        yield mock


class TestCreateJob:
    """Test POST /api/v1/jobs - Create fill job"""

    def test_create_job_success(self, client, auth_headers, mock_sheets_client):
        """Test creating fill job successfully"""
        # Mock template exists
        mock_sheets_client.get_template.return_value = {
            'id': 'tpl_123',
            'name': 'Test Template',
            'figma_file_id': 'file_123'
        }

        # Mock user exists
        mock_sheets_client.get_user_by_email.return_value = {
            'id': 'usr_123',
            'email': 'test@example.com'
        }

        # Mock job creation
        mock_sheets_client.create_fill_job.return_value = 'job_abc123'
        mock_sheets_client.log_audit.return_value = None

        headers = auth_headers()
        response = client.post('/api/v1/jobs', headers=headers, json={
            'template_id': 'tpl_123',
            'input_data': {
                'HEAD_TITLE': '春の大セール開催中',
                'SUB_TITLE': '全商品30%OFF'
            }
        })

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['job_id'] == 'job_abc123'
        assert data['status'] == 'pending'
        assert data['template_id'] == 'tpl_123'
        assert 'message' in data

        # Verify sheets_client methods were called
        mock_sheets_client.get_template.assert_called_once_with('tpl_123')
        mock_sheets_client.create_fill_job.assert_called_once()

    def test_create_job_missing_template_id(self, client, auth_headers, mock_sheets_client):
        """Test creating job without template_id"""
        headers = auth_headers()
        response = client.post('/api/v1/jobs', headers=headers, json={
            'input_data': {'title': 'Test'}
        })

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error']['code'] == 'MISSING_FIELD'
        assert 'template_id' in data['error']['message']

    def test_create_job_missing_input_data(self, client, auth_headers, mock_sheets_client):
        """Test creating job without input_data"""
        headers = auth_headers()
        response = client.post('/api/v1/jobs', headers=headers, json={
            'template_id': 'tpl_123'
        })

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error']['code'] == 'INVALID_INPUT_DATA'

    def test_create_job_invalid_input_data_type(self, client, auth_headers, mock_sheets_client):
        """Test creating job with invalid input_data type"""
        headers = auth_headers()
        response = client.post('/api/v1/jobs', headers=headers, json={
            'template_id': 'tpl_123',
            'input_data': 'not-an-object'
        })

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error']['code'] == 'INVALID_INPUT_DATA'

    def test_create_job_template_not_found(self, client, auth_headers, mock_sheets_client):
        """Test creating job with non-existent template"""
        mock_sheets_client.get_template.return_value = None

        headers = auth_headers()
        response = client.post('/api/v1/jobs', headers=headers, json={
            'template_id': 'nonexistent',
            'input_data': {'title': 'Test'}
        })

        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error']['code'] == 'TEMPLATE_NOT_FOUND'

    def test_create_job_empty_request_body(self, client, auth_headers, mock_sheets_client):
        """Test creating job with empty request body"""
        headers = auth_headers()
        response = client.post('/api/v1/jobs', headers=headers)

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error']['code'] == 'INVALID_REQUEST'

    def test_create_job_unauthorized(self, client, mock_sheets_client):
        """Test creating job without authentication"""
        response = client.post('/api/v1/jobs', json={
            'template_id': 'tpl_123',
            'input_data': {'title': 'Test'}
        })

        assert response.status_code == 401

    def test_create_job_sheets_error(self, client, auth_headers, mock_sheets_client):
        """Test creating job with sheets API error"""
        mock_sheets_client.get_template.return_value = {'id': 'tpl_123', 'name': 'Test'}
        mock_sheets_client.get_user_by_email.return_value = {'id': 'usr_123', 'email': 'test@example.com'}
        mock_sheets_client.create_fill_job.side_effect = Exception('Sheets API error')

        headers = auth_headers()
        response = client.post('/api/v1/jobs', headers=headers, json={
            'template_id': 'tpl_123',
            'input_data': {'title': 'Test'}
        })

        assert response.status_code == 500
        data = json.loads(response.data)
        assert data['error']['code'] == 'JOB_CREATION_FAILED'


class TestListJobs:
    """Test GET /api/v1/jobs - List fill jobs"""

    def test_list_jobs_success(self, client, auth_headers, mock_sheets_client):
        """Test listing jobs successfully"""
        mock_sheets_client.get_user_by_email.return_value = {
            'id': 'usr_123',
            'email': 'test@example.com'
        }

        mock_jobs = [
            {
                'job_id': 'job_1',
                'template_id': 'tpl_1',
                'status': 'completed',
                'created_at': '2025-10-16T00:00:00Z'
            },
            {
                'job_id': 'job_2',
                'template_id': 'tpl_2',
                'status': 'pending',
                'created_at': '2025-10-16T01:00:00Z'
            }
        ]

        mock_sheets_client.get_fill_jobs.return_value = mock_jobs

        headers = auth_headers()
        response = client.get('/api/v1/jobs', headers=headers)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'jobs' in data
        assert len(data['jobs']) == 2
        assert 'total' in data
        assert 'limit' in data
        assert 'offset' in data

    def test_list_jobs_with_pagination(self, client, auth_headers, mock_sheets_client):
        """Test listing jobs with pagination parameters"""
        mock_sheets_client.get_user_by_email.return_value = {'id': 'usr_123', 'email': 'test@example.com'}
        mock_sheets_client.get_fill_jobs.return_value = []

        headers = auth_headers()
        response = client.get('/api/v1/jobs?limit=10&offset=20', headers=headers)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['limit'] == 10
        assert data['offset'] == 20

        # Verify sheets_client was called with correct parameters
        calls = mock_sheets_client.get_fill_jobs.call_args_list
        assert len(calls) >= 1

    def test_list_jobs_with_status_filter(self, client, auth_headers, mock_sheets_client):
        """Test listing jobs with status filter"""
        mock_sheets_client.get_user_by_email.return_value = {'id': 'usr_123', 'email': 'test@example.com'}
        mock_sheets_client.get_fill_jobs.return_value = [
            {'job_id': 'job_1', 'status': 'completed', 'template_id': 'tpl_1'}
        ]

        headers = auth_headers()
        response = client.get('/api/v1/jobs?status=completed', headers=headers)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['jobs']) == 1
        assert data['jobs'][0]['status'] == 'completed'

    def test_list_jobs_empty_result(self, client, auth_headers, mock_sheets_client):
        """Test listing jobs when no jobs exist"""
        mock_sheets_client.get_user_by_email.return_value = {'id': 'usr_123', 'email': 'test@example.com'}
        mock_sheets_client.get_fill_jobs.return_value = []

        headers = auth_headers()
        response = client.get('/api/v1/jobs', headers=headers)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['jobs'] == []
        assert data['total'] == 0

    def test_list_jobs_unauthorized(self, client, mock_sheets_client):
        """Test listing jobs without authentication"""
        response = client.get('/api/v1/jobs')

        assert response.status_code == 401

    def test_list_jobs_sheets_error(self, client, auth_headers, mock_sheets_client):
        """Test listing jobs with sheets API error"""
        mock_sheets_client.get_user_by_email.return_value = {'id': 'usr_123', 'email': 'test@example.com'}
        mock_sheets_client.get_fill_jobs.side_effect = Exception('Sheets API error')

        headers = auth_headers()
        response = client.get('/api/v1/jobs', headers=headers)

        assert response.status_code == 500
        data = json.loads(response.data)
        assert data['error']['code'] == 'JOB_LIST_FAILED'


class TestGetJob:
    """Test GET /api/v1/jobs/<job_id> - Get job details"""

    def test_get_job_not_implemented(self, client, auth_headers, mock_sheets_client):
        """Test getting job details (not yet implemented)"""
        headers = auth_headers()
        response = client.get('/api/v1/jobs/job_123', headers=headers)

        assert response.status_code == 501
        data = json.loads(response.data)
        assert data['error']['code'] == 'NOT_IMPLEMENTED'

    def test_get_job_unauthorized(self, client, mock_sheets_client):
        """Test getting job details without authentication"""
        response = client.get('/api/v1/jobs/job_123')

        assert response.status_code == 401


class TestUpdateJob:
    """Test PATCH /api/v1/jobs/<job_id> - Update job status"""

    def test_update_job_success(self, client, auth_headers, mock_sheets_client):
        """Test updating job status successfully"""
        mock_sheets_client.update_fill_job.return_value = None
        mock_sheets_client.log_audit.return_value = None

        headers = auth_headers()
        response = client.patch('/api/v1/jobs/job_123', headers=headers, json={
            'status': 'completed',
            'result_urls': ['https://example.com/result.png']
        })

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['job_id'] == 'job_123'
        assert data['status'] == 'completed'
        assert 'message' in data

        # Verify sheets_client methods were called
        mock_sheets_client.update_fill_job.assert_called_once_with(
            'job_123',
            'completed',
            ['https://example.com/result.png']
        )

    def test_update_job_status_pending(self, client, auth_headers, mock_sheets_client):
        """Test updating job status to pending"""
        mock_sheets_client.update_fill_job.return_value = None
        mock_sheets_client.log_audit.return_value = None

        headers = auth_headers()
        response = client.patch('/api/v1/jobs/job_123', headers=headers, json={
            'status': 'pending'
        })

        assert response.status_code == 200

    def test_update_job_status_processing(self, client, auth_headers, mock_sheets_client):
        """Test updating job status to processing"""
        mock_sheets_client.update_fill_job.return_value = None
        mock_sheets_client.log_audit.return_value = None

        headers = auth_headers()
        response = client.patch('/api/v1/jobs/job_123', headers=headers, json={
            'status': 'processing'
        })

        assert response.status_code == 200

    def test_update_job_status_failed(self, client, auth_headers, mock_sheets_client):
        """Test updating job status to failed"""
        mock_sheets_client.update_fill_job.return_value = None
        mock_sheets_client.log_audit.return_value = None

        headers = auth_headers()
        response = client.patch('/api/v1/jobs/job_123', headers=headers, json={
            'status': 'failed'
        })

        assert response.status_code == 200

    def test_update_job_invalid_status(self, client, auth_headers, mock_sheets_client):
        """Test updating job with invalid status"""
        headers = auth_headers()
        response = client.patch('/api/v1/jobs/job_123', headers=headers, json={
            'status': 'invalid_status'
        })

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error']['code'] == 'INVALID_STATUS'

    def test_update_job_without_result_urls(self, client, auth_headers, mock_sheets_client):
        """Test updating job without result_urls"""
        mock_sheets_client.update_fill_job.return_value = None
        mock_sheets_client.log_audit.return_value = None

        headers = auth_headers()
        response = client.patch('/api/v1/jobs/job_123', headers=headers, json={
            'status': 'completed'
        })

        assert response.status_code == 200
        # Verify update_fill_job was called with None for result_urls
        mock_sheets_client.update_fill_job.assert_called_once_with('job_123', 'completed', None)

    def test_update_job_empty_request_body(self, client, auth_headers, mock_sheets_client):
        """Test updating job with empty request body"""
        headers = auth_headers()
        response = client.patch('/api/v1/jobs/job_123', headers=headers)

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error']['code'] == 'INVALID_REQUEST'

    def test_update_job_unauthorized(self, client, mock_sheets_client):
        """Test updating job without authentication"""
        response = client.patch('/api/v1/jobs/job_123', json={
            'status': 'completed'
        })

        assert response.status_code == 401

    def test_update_job_sheets_error(self, client, auth_headers, mock_sheets_client):
        """Test updating job with sheets API error"""
        mock_sheets_client.update_fill_job.side_effect = Exception('Sheets API error')

        headers = auth_headers()
        response = client.patch('/api/v1/jobs/job_123', headers=headers, json={
            'status': 'completed'
        })

        assert response.status_code == 500
        data = json.loads(response.data)
        assert data['error']['code'] == 'UPDATE_FAILED'


class TestJobsIntegration:
    """Integration tests for jobs workflow"""

    def test_full_job_lifecycle(self, client, auth_headers, mock_sheets_client):
        """Test complete job lifecycle: create -> list -> update"""
        # Setup mocks
        mock_sheets_client.get_template.return_value = {
            'id': 'tpl_123',
            'name': 'Test Template'
        }
        mock_sheets_client.get_user_by_email.return_value = {
            'id': 'usr_123',
            'email': 'test@example.com'
        }
        mock_sheets_client.create_fill_job.return_value = 'job_abc123'
        mock_sheets_client.log_audit.return_value = None

        headers = auth_headers()

        # Step 1: Create job
        create_response = client.post('/api/v1/jobs', headers=headers, json={
            'template_id': 'tpl_123',
            'input_data': {'title': 'Test'}
        })
        assert create_response.status_code == 201
        job_data = json.loads(create_response.data)
        job_id = job_data['job_id']

        # Step 2: List jobs
        mock_sheets_client.get_fill_jobs.return_value = [{
            'job_id': job_id,
            'template_id': 'tpl_123',
            'status': 'pending'
        }]

        list_response = client.get('/api/v1/jobs', headers=headers)
        assert list_response.status_code == 200
        list_data = json.loads(list_response.data)
        assert any(job['job_id'] == job_id for job in list_data['jobs'])

        # Step 3: Update job status
        mock_sheets_client.update_fill_job.return_value = None

        update_response = client.patch(f'/api/v1/jobs/{job_id}', headers=headers, json={
            'status': 'completed',
            'result_urls': ['https://result.png']
        })
        assert update_response.status_code == 200

    def test_audit_logging_for_job_operations(self, client, auth_headers, mock_sheets_client):
        """Test that audit logs are created for job operations"""
        mock_sheets_client.get_template.return_value = {'id': 'tpl_123', 'name': 'Test'}
        mock_sheets_client.get_user_by_email.return_value = {'id': 'usr_123', 'email': 'test@example.com'}
        mock_sheets_client.create_fill_job.return_value = 'job_123'
        mock_sheets_client.log_audit.return_value = None

        headers = auth_headers()

        # Create job
        client.post('/api/v1/jobs', headers=headers, json={
            'template_id': 'tpl_123',
            'input_data': {'title': 'Test'}
        })

        # Verify audit log was called
        assert mock_sheets_client.log_audit.call_count >= 1
        audit_calls = mock_sheets_client.log_audit.call_args_list
        assert any('job.created' in str(call) for call in audit_calls)

        # Update job
        mock_sheets_client.update_fill_job.return_value = None
        client.patch('/api/v1/jobs/job_123', headers=headers, json={
            'status': 'completed'
        })

        # Verify audit log was called again
        assert mock_sheets_client.log_audit.call_count >= 2
