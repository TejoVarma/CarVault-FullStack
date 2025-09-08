# app/models/user.py - Final User Model
import uuid
from sqlalchemy import Boolean, Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    __tablename__ = "users"

    # PRIMARY KEY (UUID for security)
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # === REQUIRED SIGNUP FIELDS ===
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)  # NEVER store plain passwords
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)

    # === OPTIONAL SIGNUP FIELDS ===
    phone = Column(
        String(20), nullable=True
    )  # Optional for users, required for admins (UI handles this)

    # === USER TYPE & STATUS ===
    is_admin = Column(
        Boolean, default=False, nullable=False, index=True
    )  # False=User, True=Admin
    is_active = Column(
        Boolean, default=True, nullable=False, index=True
    )  # Account status

    # === OPTIONAL PROFILE FIELDS ===
    # Personal Information
    date_of_birth = Column(DateTime, nullable=True)
    profile_picture_url = Column(String(500), nullable=True)

    # Address Information (All optional - filled via profile page)
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(100), nullable=True)

    # Emergency Contact (Optional)
    emergency_contact_name = Column(String(200), nullable=True)
    emergency_contact_phone = Column(String(20), nullable=True)
    emergency_contact_relationship = Column(
        String(50), nullable=True
    )  # "Mother", "Friend", etc.

    # === AUTOMATIC TIMESTAMPS ===
    created_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )
    last_login = Column(DateTime, nullable=True)  # Track user activity

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, admin={self.is_admin})>"

    @property
    def full_name(self):
        """Convenience property to get full name"""
        return f"{self.first_name} {self.last_name}"
