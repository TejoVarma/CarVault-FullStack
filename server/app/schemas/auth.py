from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime


class UserRegister(BaseModel):
    """Schema for user registration"""

    email: EmailStr
    password: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    is_admin: bool = False

    @validator("password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v

    @validator("first_name", "last_name")
    def validate_names(cls, v):
        if not v.strip():
            raise ValueError("Name cannot be empty")
        if len(v.strip()) < 2:
            raise ValueError("Name must be at least 2 characters long")
        return v.strip().title()  # Capitalize properly

    @validator("phone")
    def validate_phone(cls, v):
        if v is not None and v.strip():
            # Basic phone validation
            cleaned = "".join(filter(str.isdigit, v))
            if len(cleaned) < 10:
                raise ValueError("Phone number must contain at least 10 digits")
        return v


class UserLogin(BaseModel):
    """Schema for user login"""

    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for user data in responses (no sensitive info)"""

    id: str
    email: str
    first_name: str
    last_name: str
    full_name: str
    phone: Optional[str]
    is_admin: bool
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    """Schema for successful login response"""

    message: str
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds (86400 = 24 hours)
    user: UserResponse


class PasswordChange(BaseModel):
    """Schema for password change"""

    current_password: str
    new_password: str

    @validator("new_password")
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserProfile(BaseModel):
    """Schema for complete user profile data"""

    id: str
    email: str
    first_name: str
    last_name: str
    full_name: str
    phone: Optional[str]
    is_admin: bool
    is_active: bool
    date_of_birth: Optional[datetime]
    profile_picture_url: Optional[str]
    address_line1: Optional[str]
    address_line2: Optional[str]
    city: Optional[str]
    state: Optional[str]
    postal_code: Optional[str]
    country: Optional[str]
    emergency_contact_name: Optional[str]
    emergency_contact_phone: Optional[str]
    emergency_contact_relationship: Optional[str]
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime]

    class Config:
        from_attributes = True
