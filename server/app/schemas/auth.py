from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List, Dict
from datetime import datetime


class UserRegister(BaseModel):
    """Schema for user registration"""

    email: EmailStr
    password: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    initial_role: str = "customer"  # "customer" or "car_owner"

    @validator("initial_role")
    def validate_initial_role(cls, v):
        if v not in ("customer", "car_owner"):
            raise ValueError("Initial role must be 'customer' or 'car_owner'")
        return v

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
    roles: List[str]
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]

    # Helper flags, computed from `roles` (see User model properties)
    is_customer: bool = False
    is_car_owner: bool = False
    business_name: Optional[str] = None

    @validator("id", pre=True)
    def convert_id_to_str(cls, v):
        # new_user.id is a Python UUID object (see models/user.py); model_validate()
        # reads it as-is, unlike the old manual `str(new_user.id)` construction.
        return str(v)

    class Config:
        from_attributes = True


class BusinessProfileCreate(BaseModel):
    """Schema for becoming a car owner"""

    business_name: str
    business_description: Optional[str] = None
    business_phone: str
    pickup_instructions: Optional[str] = None

    @validator("business_name")
    def validate_business_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError("Business name must be at least 2 characters")
        return v.strip()


class CustomerProfileUpdate(BaseModel):
    """Schema for updating customer preferences"""

    rental_preferences: Optional[Dict] = None
    communication_preferences: Optional[Dict] = None


class BusinessProfileUpdate(BaseModel):
    """Schema for updating business profile"""

    business_name: Optional[str] = None
    business_description: Optional[str] = None
    business_phone: Optional[str] = None
    pickup_instructions: Optional[str] = None


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
    roles: List[str]
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
