"""
User Pydantic schemas for request/response validation.
"""
from typing import Optional

from pydantic import BaseModel, EmailStr, ConfigDict


# Shared properties
class UserBase(BaseModel):
    """Base user schema with common properties."""
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False
    strava_access_token: Optional[str] = None
    strava_refresh_token: Optional[str] = None
    strava_athlete_id: Optional[int] = None
    strava_token_expires_at: Optional[int] = None


# Properties to receive via API on creation
class UserCreate(UserBase):
    """Schema for user creation."""
    password: str


# Properties to receive via API on update
class UserUpdate(UserBase):
    """Schema for user update."""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: Optional[str] = None


# Additional properties to return via API
class User(UserBase):
    """Schema for user response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int


# Additional properties stored in DB
class UserInDB(User):
    """Schema for user in database."""
    hashed_password: str


# Token schemas
class Token(BaseModel):
    """Token response schema."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token data schema."""
    username: Optional[str] = None