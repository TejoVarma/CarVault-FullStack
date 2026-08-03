from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime
from decimal import Decimal
from app.models.car import CAR_CATEGORIES

CURRENT_YEAR = datetime.utcnow().year


class CarCreate(BaseModel):
    """Schema for a car owner listing a new car"""

    make: str
    model: str
    year: int
    category: str
    city: str
    state: Optional[str] = None
    daily_rate: Decimal
    description: Optional[str] = None

    @validator("category")
    def validate_category(cls, v):
        if v not in CAR_CATEGORIES:
            raise ValueError(f"Category must be one of: {', '.join(CAR_CATEGORIES)}")
        return v

    @validator("year")
    def validate_year(cls, v):
        if v < 1980 or v > CURRENT_YEAR + 1:
            raise ValueError(f"Year must be between 1980 and {CURRENT_YEAR + 1}")
        return v

    @validator("daily_rate")
    def validate_daily_rate(cls, v):
        if v <= 0:
            raise ValueError("Daily rate must be greater than 0")
        return v

    @validator("make", "model", "city")
    def validate_not_blank(cls, v):
        if not v.strip():
            raise ValueError("This field cannot be blank")
        return v.strip()


class CarUpdate(BaseModel):
    """Schema for editing a car — all fields optional (partial update, see learning-notes/16)"""

    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    category: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    daily_rate: Optional[Decimal] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

    @validator("category")
    def validate_category(cls, v):
        if v is not None and v not in CAR_CATEGORIES:
            raise ValueError(f"Category must be one of: {', '.join(CAR_CATEGORIES)}")
        return v

    @validator("year")
    def validate_year(cls, v):
        if v is not None and (v < 1980 or v > CURRENT_YEAR + 1):
            raise ValueError(f"Year must be between 1980 and {CURRENT_YEAR + 1}")
        return v

    @validator("daily_rate")
    def validate_daily_rate(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Daily rate must be greater than 0")
        return v


class CarResponse(BaseModel):
    """Schema for car data in responses"""

    id: str
    owner_id: str
    make: str
    model: str
    year: int
    category: str
    city: str
    state: Optional[str]
    daily_rate: Decimal
    description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @validator("id", "owner_id", pre=True)
    def convert_uuid_to_str(cls, v):
        # Same UUID-to-str gotcha as UserResponse — see learning-notes/15.
        return str(v)

    class Config:
        from_attributes = True
