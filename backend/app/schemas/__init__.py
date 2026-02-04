"""
Pydantic schemas for request/response validation.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, ConfigDict


# =============================================================================
# Base Schemas
# =============================================================================
class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )


# =============================================================================
# User Schemas
# =============================================================================
class UserCreate(BaseModel):
    """Schema for user registration."""
    
    email: EmailStr
    password: str = Field(min_length=8, max_length=100)
    full_name: Optional[str] = Field(None, max_length=255)


class UserLogin(BaseModel):
    """Schema for user login."""
    
    email: EmailStr
    password: str


class UserResponse(BaseSchema):
    """Schema for user response."""
    
    id: int
    email: str
    full_name: Optional[str]
    is_active: bool
    is_verified: bool
    created_at: datetime


class UserUpdate(BaseModel):
    """Schema for user update."""
    
    full_name: Optional[str] = Field(None, max_length=255)
    password: Optional[str] = Field(None, min_length=8, max_length=100)


# =============================================================================
# Auth Schemas
# =============================================================================
class TokenResponse(BaseModel):
    """Schema for authentication token response."""
    
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    """Schema for token refresh request."""
    
    refresh_token: str


# =============================================================================
# Project Schemas
# =============================================================================
class ProjectCreate(BaseModel):
    """Schema for creating a project."""
    
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    location_name: Optional[str] = Field(None, max_length=500)


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    location_name: Optional[str] = Field(None, max_length=500)


class ProjectResponse(BaseSchema):
    """Schema for project response."""
    
    id: int
    name: str
    description: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    location_name: Optional[str]
    status: int
    status_name: str
    task_id: Optional[str]
    image_count: int
    total_size_bytes: int
    pci_score: Optional[float]
    results: Optional[dict]
    processing_started_at: Optional[datetime]
    processing_completed_at: Optional[datetime]
    processing_error: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]


class ProjectListResponse(BaseSchema):
    """Schema for project list response (lighter than full response)."""
    
    id: int
    name: str
    status: int
    status_name: str
    image_count: int
    pci_score: Optional[float]
    created_at: datetime


# =============================================================================
# Image Schemas
# =============================================================================
class ImageResponse(BaseSchema):
    """Schema for image response."""
    
    id: int
    project_id: int
    original_filename: str
    storage_key: str
    url: str
    content_type: str
    size_bytes: int
    width: Optional[int]
    height: Optional[int]
    processed: bool
    analysis_results: Optional[dict]
    created_at: datetime
    processed_at: Optional[datetime]


class ImageUploadResponse(BaseModel):
    """Schema for image upload response."""
    
    uploaded: int
    failed: int
    images: list[ImageResponse]
    errors: list[str]


# =============================================================================
# Analysis Schemas
# =============================================================================
class AnalysisStartResponse(BaseModel):
    """Schema for analysis start response."""
    
    project_id: int
    task_id: str
    status: str
    message: str


class AnalysisStatusResponse(BaseModel):
    """Schema for analysis status response."""
    
    task_id: str
    status: str
    progress: int = Field(ge=0, le=100)
    message: str
    result: Optional[dict] = None


class AnalysisResultResponse(BaseModel):
    """Schema for analysis result."""
    
    project_id: int
    pci_score: float
    defect_count: int
    defect_area_percentage: float
    severity_distribution: dict
    processed_images: int
    processing_time_seconds: float
    details: Optional[dict] = None


# =============================================================================
# Pagination Schemas
# =============================================================================
class PaginatedResponse(BaseModel):
    """Generic paginated response."""
    
    items: list
    total: int
    page: int
    size: int
    pages: int


class PaginationParams(BaseModel):
    """Pagination parameters."""
    
    page: int = Field(1, ge=1)
    size: int = Field(20, ge=1, le=100)
    
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size


# =============================================================================
# Common Schemas
# =============================================================================
class MessageResponse(BaseModel):
    """Generic message response."""
    
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    """Error response."""
    
    detail: str
    error_code: Optional[str] = None
