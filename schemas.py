"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


# Authentication Schemas
class UserRegister(BaseModel):
    """User registration schema"""
    phone: str = Field(..., min_length=10, max_length=20, description="Phone number (mandatory)")
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=8)
    email: Optional[EmailStr] = None  # Optional
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    """User login schema"""
    username: str  # Can be username or email
    password: str


class Token(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token payload data"""
    user_id: Optional[int] = None


# User Schemas
class UserBase(BaseModel):
    """Base user schema"""
    phone: str
    email: Optional[str] = None
    username: str
    full_name: Optional[str] = None
    is_active: bool = True


class UserCreate(UserBase):
    """User creation schema"""
    password: str


class UserResponse(UserBase):
    """User response schema"""
    id: int
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Phone validation helper
def validate_phone(phone: str) -> str:
    """Validate and normalize phone number"""
    # Remove spaces, dashes, parentheses
    phone = ''.join(filter(str.isdigit, phone))
    if len(phone) < 10:
        raise ValueError("Phone number must be at least 10 digits")
    return phone


# User Preferences Schemas
class UserPreferenceBase(BaseModel):
    """Base preference schema"""
    language: str = "English"
    theme: str = "light"
    default_location: Optional[str] = None
    default_max_articles: int = 10
    email_notifications: bool = False


class UserPreferenceCreate(UserPreferenceBase):
    """Preference creation schema"""
    pass


class UserPreferenceResponse(UserPreferenceBase):
    """Preference response schema"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Search History Schemas
class SearchHistoryBase(BaseModel):
    """Base search history schema"""
    query: str
    location: Optional[str] = None
    max_articles: Optional[int] = None
    language: Optional[str] = None
    when_filter: Optional[str] = None


class SearchHistoryCreate(SearchHistoryBase):
    """Search history creation schema"""
    pass


class SearchHistoryResponse(SearchHistoryBase):
    """Search history response schema"""
    id: int
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

