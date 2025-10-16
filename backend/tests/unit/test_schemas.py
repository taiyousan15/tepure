"""
Unit tests for Pydantic schemas
"""
import pytest
from pydantic import ValidationError
from app.schemas import (
    LoginRequest,
    JobCreateRequest,
    TemplateCreateRequest,
    UserSchema
)


def test_login_request_valid():
    """Test valid login request"""
    data = {
        'email': 'user@example.com',
        'password': 'password123'
    }

    request = LoginRequest(**data)
    assert request.email == 'user@example.com'
    assert request.password == 'password123'


def test_login_request_invalid_email():
    """Test invalid email format"""
    data = {
        'email': 'not-an-email',
        'password': 'password123'
    }

    with pytest.raises(ValidationError):
        LoginRequest(**data)


def test_login_request_password_too_short():
    """Test password too short"""
    data = {
        'email': 'user@example.com',
        'password': 'short'
    }

    with pytest.raises(ValidationError):
        LoginRequest(**data)


def test_job_create_request_valid():
    """Test valid job creation request"""
    data = {
        'template_id': 'tpl_123',
        'inputs': {'title': 'Hello', 'description': 'World'},
        'temperature': 0.7,
        'intensity': 'medium'
    }

    request = JobCreateRequest(**data)
    assert request.template_id == 'tpl_123'
    assert request.inputs == {'title': 'Hello', 'description': 'World'}
    assert request.temperature == 0.7
    assert request.intensity == 'medium'


def test_job_create_request_empty_inputs():
    """Test empty inputs raises error"""
    data = {
        'template_id': 'tpl_123',
        'inputs': {},
        'temperature': 0.7,
        'intensity': 'medium'
    }

    with pytest.raises(ValidationError):
        JobCreateRequest(**data)


def test_job_create_request_invalid_temperature():
    """Test invalid temperature"""
    data = {
        'template_id': 'tpl_123',
        'inputs': {'title': 'Hello'},
        'temperature': 1.5,  # Out of range
        'intensity': 'medium'
    }

    with pytest.raises(ValidationError):
        JobCreateRequest(**data)


def test_job_create_request_invalid_intensity():
    """Test invalid intensity"""
    data = {
        'template_id': 'tpl_123',
        'inputs': {'title': 'Hello'},
        'temperature': 0.7,
        'intensity': 'extreme'  # Invalid value
    }

    with pytest.raises(ValidationError):
        JobCreateRequest(**data)


def test_template_create_request_valid():
    """Test valid template creation"""
    data = {
        'name': 'Test Template',
        'figma_file_key': 'abc123xyz',
        'category': 'social-media',
        'tags': ['instagram', 'story']
    }

    request = TemplateCreateRequest(**data)
    assert request.name == 'Test Template'
    assert request.figma_file_key == 'abc123xyz'
    assert len(request.tags) == 2


def test_template_create_request_tags_from_string():
    """Test tags parsing from comma-separated string"""
    data = {
        'name': 'Test Template',
        'figma_file_key': 'abc123xyz',
        'tags': 'instagram, story, marketing'
    }

    request = TemplateCreateRequest(**data)
    assert len(request.tags) == 3
    assert 'instagram' in request.tags
    assert 'story' in request.tags


def test_user_schema_valid():
    """Test valid user schema"""
    from datetime import datetime

    data = {
        'id': 'usr_123',
        'email': 'user@example.com',
        'role': 'user',
        'monthly_quota': 100,
        'created_at': datetime.utcnow().isoformat()
    }

    user = UserSchema(**data)
    assert user.id == 'usr_123'
    assert user.role == 'user'
    assert user.monthly_quota == 100
