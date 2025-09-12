from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from enum import Enum

class ApplicationStatus(str, Enum):
    """Enumeration for application statuses"""
    applied = "applied"
    interviewing = "interviewing"
    rejected = "rejected"
    offer = "offer"
    archived = "archived"

# ===== USER SCHEMAS =====
class UserCreate(BaseModel):
    """Schema for creating a new user (request body)"""
    email: EmailStr  # Validates email format
    full_name: Optional[str] = Field(default=None, max_length=255)

class UserOut(BaseModel):
    """Schema for user response (output)"""
    id: int
    email: EmailStr
    full_name: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Allows conversion from SQLAlchemy model

# ===== APPLICATION SCHEMAS =====
class ApplicationCreate(BaseModel):
    """Schema for creating a new application (request body)"""
    user_id: int
    company: str = Field(min_length=1, max_length=255)
    role_title: str = Field(min_length=1, max_length=255)
    source: Optional[str] = Field(default=None, max_length=100)
    status: Optional[ApplicationStatus] = ApplicationStatus.applied
    job_url: Optional[str] = None
    notes: Optional[str] = None

class ApplicationOut(BaseModel):
    """Schema for application response (output)"""
    id: int
    user_id: int
    company: str
    role_title: str
    source: Optional[str]
    status: ApplicationStatus
    job_url: Optional[str]
    notes: Optional[str]
    applied_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Allows conversion from SQLAlchemy model

class ApplicationsList(BaseModel):
    """Schema for paginated list of applications"""
    items: List[ApplicationOut]
    total: int
    limit: int
    offset: int

# ===== API KEY SCHEMAS =====
class ApiKeyCreate(BaseModel):
    """Schema for creating an API key"""
    user_id: int
    name: str = Field(min_length=1, max_length=100)

class ApiKeyOut(BaseModel):
    """Schema for API key response (without secret)"""
    id: int
    user_id: int
    name: str
    prefix: str
    is_active: bool
    created_at: datetime
    last_used_at: Optional[datetime]

    class Config:
        from_attributes = True

class ApiKeyWithToken(ApiKeyOut):
    """Schema for API key response with token (only on create)"""
    token: str  # Only returned on creation