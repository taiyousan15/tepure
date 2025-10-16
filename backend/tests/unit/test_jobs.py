"""
Unit tests for job queue module
"""
import pytest
from app.jobs import JobQueue


@pytest.fixture
def job_queue():
    """Create fresh job queue for each test"""
    return JobQueue()


def test_create_job(job_queue, mocker):
    """Test job creation"""
    # Mock sheets client
    mocker.patch.object(job_queue, 'sheets_client')

    job_id = job_queue.create_job(
        user_id='user_123',
        template_id='tpl_123',
        inputs={'title': 'Test'},
        temperature=0.7,
        intensity='medium'
    )

    assert job_id is not None
    assert job_id.startswith('job_')

    # Verify job was created
    job = job_queue.get_job_status(job_id)
    assert job is not None
    assert job['status'] == 'pending'
    assert job['user_id'] == 'user_123'
    assert job['template_id'] == 'tpl_123'


def test_idempotency(job_queue, mocker):
    """Test idempotency key prevents duplicate jobs"""
    mocker.patch.object(job_queue, 'sheets_client')

    idempotency_key = 'test_key_123'

    # Create first job
    job_id_1 = job_queue.create_job(
        user_id='user_123',
        template_id='tpl_123',
        inputs={'title': 'Test'},
        idempotency_key=idempotency_key
    )

    # Create second job with same key
    job_id_2 = job_queue.create_job(
        user_id='user_123',
        template_id='tpl_123',
        inputs={'title': 'Test'},
        idempotency_key=idempotency_key
    )

    # Should return same job ID
    assert job_id_1 == job_id_2


def test_update_job_status(job_queue, mocker):
    """Test job status update"""
    mocker.patch.object(job_queue, 'sheets_client')

    job_id = job_queue.create_job(
        user_id='user_123',
        template_id='tpl_123',
        inputs={'title': 'Test'}
    )

    # Update to processing
    job_queue.update_job_status(job_id, 'processing')
    job = job_queue.get_job_status(job_id)
    assert job['status'] == 'processing'

    # Update to completed
    result = {'output': 'Generated content'}
    usage = {'prompt_tokens': 100, 'completion_tokens': 200, 'total_tokens': 300}

    job_queue.update_job_status(job_id, 'completed', result=result, usage=usage)
    job = job_queue.get_job_status(job_id)

    assert job['status'] == 'completed'
    assert job['result'] == result
    assert job['usage'] == usage
    assert job['completed_at'] is not None


def test_get_job_not_found(job_queue):
    """Test getting non-existent job"""
    job = job_queue.get_job_status('nonexistent_job')
    assert job is None


def test_get_job_count_by_status(job_queue, mocker):
    """Test counting jobs by status"""
    mocker.patch.object(job_queue, 'sheets_client')

    # Create multiple jobs
    job_id_1 = job_queue.create_job('user_123', 'tpl_123', {'title': 'Test 1'})
    job_id_2 = job_queue.create_job('user_123', 'tpl_123', {'title': 'Test 2'})

    # All should be pending
    assert job_queue.get_job_count_by_status('pending') == 2

    # Update one to completed
    job_queue.update_job_status(job_id_1, 'completed')

    assert job_queue.get_job_count_by_status('pending') == 1
    assert job_queue.get_job_count_by_status('completed') == 1
