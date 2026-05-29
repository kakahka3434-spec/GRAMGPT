"""
User models for GRAMGPT authentication and authorization.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    """Request model for user registration."""
    email: EmailStr
    password: str = Field(..., min_length=8, description="Minimum 8 characters")
    username: Optional[str] = None


class UserResponse(BaseModel):
    """Response model for user data (no password)."""
    id: str
    email: str
    username: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Response model for authentication tokens."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenRequest(BaseModel):
    """Request model for login."""
    email: str
    password: str
