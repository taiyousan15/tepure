"""
Pydantic schemas for request/response validation
"""
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, validator, root_validator


# ========== User Schemas ==========

class UserSchema(BaseModel):
    """User model"""
    id: str
    email: EmailStr
    role: Literal['user', 'admin'] = 'user'
    monthly_quota: int = Field(default=100, ge=0)
    created_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "id": "usr_20251016120000000",
                "email": "user@example.com",
                "role": "user",
                "monthly_quota": 100,
                "created_at": "2025-10-16T12:00:00Z"
            }
        }


class LoginRequest(BaseModel):
    """Login request"""
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginResponse(BaseModel):
    """Login response with JWT tokens"""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = 900  # seconds


class RefreshRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str


# ========== Template Schemas ==========

class Field(BaseModel):
    """Field definition for template inputs"""
    type: Literal['text', 'color', 'border']
    label: str = Field(min_length=1, max_length=100)
    default_value: Any

    class Config:
        json_schema_extra = {
            "example": {
                "type": "text",
                "label": "Title",
                "default_value": "Enter title here"
            }
        }


class TemplateSchema(BaseModel):
    """Template model (extended schema with category, fields, preview_url)"""
    id: str
    name: str = Field(min_length=1, max_length=200)
    figma_file_key: str = Field(min_length=1, max_length=100)
    figma_node_id: Optional[str] = Field(None, max_length=100)
    category: Literal['LP', 'Banner', 'SNS', 'WebApp'] = 'LP'
    tags: List[str] = Field(default_factory=list, max_items=10)
    preview_url: Optional[str] = None
    fields: List[Field] = Field(default_factory=list)
    version: str = Field(default='1.0.0', regex=r'^\d+\.\d+\.\d+$')
    created_at: datetime
    updated_at: Optional[datetime] = None

    @validator('tags', pre=True)
    def validate_tags(cls, v):
        if isinstance(v, str):
            return [tag.strip() for tag in v.split(',') if tag.strip()]
        return v

    @validator('fields', pre=True)
    def validate_fields(cls, v):
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except:
                return []
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "id": "tpl_20251016120000000",
                "name": "Instagram Story Template",
                "figma_file_key": "abc123xyz",
                "figma_node_id": "1:234",
                "category": "SNS",
                "tags": ["instagram", "story", "marketing"],
                "preview_url": "https://example.com/thumb.png",
                "fields": [
                    {"type": "text", "label": "Title", "default_value": "Sample Title"},
                    {"type": "color", "label": "Background Color", "default_value": "#FF5733"},
                    {"type": "border", "label": "Border Style", "default_value": "solid"}
                ],
                "version": "1.0.0",
                "created_at": "2025-10-16T12:00:00Z"
            }
        }


class TemplateCreateRequest(BaseModel):
    """Create template request"""
    name: str = Field(min_length=1, max_length=200)
    figma_file_key: str = Field(min_length=1, max_length=100)
    figma_node_id: Optional[str] = Field(None, max_length=100)
    category: Literal['LP', 'Banner', 'SNS', 'WebApp'] = 'LP'
    tags: List[str] = Field(default_factory=list, max_items=10)
    preview_url: Optional[str] = None
    fields: List[Field] = Field(default_factory=list)


class TemplateUpdateRequest(BaseModel):
    """Update template request"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    figma_file_key: Optional[str] = Field(None, min_length=1, max_length=100)
    figma_node_id: Optional[str] = Field(None, max_length=100)
    category: Optional[Literal['LP', 'Banner', 'SNS', 'WebApp']] = None
    tags: Optional[List[str]] = Field(None, max_items=10)
    preview_url: Optional[str] = None
    fields: Optional[List[Field]] = None


class TemplateListResponse(BaseModel):
    """Template list response with pagination"""
    templates: List[TemplateSchema]
    total: int
    page: int
    size: int
    has_next: bool


# ========== Job Schemas ==========

class JobCreateRequest(BaseModel):
    """Job creation request"""
    template_id: str = Field(min_length=1, max_length=100)
    inputs: Dict[str, Any] = Field(default_factory=dict)
    temperature: float = Field(default=0.7, ge=0.0, le=1.0)
    intensity: int = Field(default=5, ge=1, le=10, description="Generation intensity from 1 (low) to 10 (high)")
    idempotency_key: Optional[str] = Field(None, min_length=1, max_length=128)

    @validator('inputs')
    def validate_inputs(cls, v):
        if not v:
            raise ValueError('inputs cannot be empty')
        if len(str(v)) > 10000:  # Limit JSON size
            raise ValueError('inputs payload too large (max 10KB)')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "template_id": "tpl_20251016120000000",
                "inputs": {
                    "title": "New Product Launch",
                    "description": "Check out our latest product!",
                    "cta": "Learn More"
                },
                "temperature": 0.7,
                "intensity": 7,
                "idempotency_key": "client-generated-uuid-12345"
            }
        }


class JobUsage(BaseModel):
    """Token usage information"""
    prompt_tokens: int = Field(ge=0)
    completion_tokens: int = Field(ge=0)
    total_tokens: int = Field(ge=0)
    estimated_cost_usd: float = Field(ge=0.0)


class JobResponse(BaseModel):
    """Job response"""
    job_id: str
    status: Literal['pending', 'processing', 'completed', 'failed']
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    usage: Optional[JobUsage] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "job_20251016120000000",
                "status": "completed",
                "result": {
                    "figma_url": "https://figma.com/file/...",
                    "preview_url": "https://example.com/preview.png",
                    "variations": []
                },
                "usage": {
                    "prompt_tokens": 150,
                    "completion_tokens": 300,
                    "total_tokens": 450,
                    "estimated_cost_usd": 0.0045
                },
                "created_at": "2025-10-16T12:00:00Z",
                "updated_at": "2025-10-16T12:00:15Z",
                "completed_at": "2025-10-16T12:00:15Z"
            }
        }


# ========== Metrics & Audit Schemas ==========

class MetricsResponse(BaseModel):
    """System metrics response"""
    success_rate: float = Field(ge=0.0, le=1.0)
    average_latency_ms: float = Field(ge=0.0)
    daily_generation_count: int = Field(ge=0)
    total_jobs_today: int = Field(ge=0)
    failed_jobs_today: int = Field(ge=0)
    timestamp: datetime


class AuditLogEntry(BaseModel):
    """Audit log entry"""
    id: str
    timestamp: datetime
    user_id: str
    action: str
    entity_type: str
    entity_id: str
    ip_address: Optional[str] = None
    latency_ms: Optional[int] = None
    tokens_used: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "log_20251016120000000",
                "timestamp": "2025-10-16T12:00:00Z",
                "user_id": "usr_20251016120000000",
                "action": "job.created",
                "entity_type": "job",
                "entity_id": "job_20251016120000000",
                "ip_address": "192.168.1.1",
                "latency_ms": 150,
                "tokens_used": 450,
                "metadata": {"template_id": "tpl_123"}
            }
        }


class AuditLogListResponse(BaseModel):
    """Audit log list response"""
    logs: List[AuditLogEntry]
    total: int
    page: int
    size: int


# ========== Error Schemas ==========

class ErrorResponse(BaseModel):
    """Standardized error response"""
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid request parameters",
                "details": {
                    "field": "inputs",
                    "error": "Field required"
                }
            }
        }
