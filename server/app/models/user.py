import uuid
from sqlalchemy import Boolean, Column, String, DateTime
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
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
    is_active = Column(
        Boolean, default=True, nullable=False, index=True
    )  # Account status

    # === DUAL ROLE SYSTEM ===
    # A user can hold multiple roles at once, e.g. ["customer", "car_owner"].
    # default is a callable (lambda), not a plain list literal, so every row
    # gets its own independent list object rather than sharing one mutable
    # default across rows.
    roles = Column(
        ARRAY(String), default=lambda: ["customer"], nullable=False, index=True
    )
    customer_profile = Column(JSONB, nullable=True)  # rental preferences, etc.
    business_profile = Column(JSONB, nullable=True)  # business_name, phone, policies
    business_verified = Column(Boolean, default=False, nullable=False)
    date_became_car_owner = Column(DateTime, nullable=True)

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
        return f"<User(id={self.id}, email={self.email}, roles={self.roles})>"

    @property
    def full_name(self):
        """Convenience property to get full name"""
        return f"{self.first_name} {self.last_name}"

    @property
    def is_customer(self) -> bool:
        return "customer" in (self.roles or [])

    @property
    def is_car_owner(self) -> bool:
        return "car_owner" in (self.roles or [])

    @property
    def business_name(self) -> str:
        if self.business_profile:
            business_info = self.business_profile.get("business_info", {})
            name = business_info.get("business_name")
            if name:
                return name
        return f"{self.first_name}'s Car Rentals"

    def has_role(self, role: str) -> bool:
        return role in (self.roles or [])

    def add_role(self, role: str):
        if not self.roles:
            self.roles = []
        if role not in self.roles:
            # Reassign rather than .append() — SQLAlchemy only detects a
            # column as "changed" on reassignment, not on in-place mutation
            # of a list it's already tracking.
            self.roles = self.roles + [role]
