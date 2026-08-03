import uuid
from sqlalchemy import Boolean, Column, String, Integer, Numeric, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

# Kept as a plain allowlist rather than a separate Category table — there's
# no need for a "manage categories" admin feature, and Postgres/SQLAlchemy
# doesn't need a whole extra table + join just to constrain a string to a
# known set of values (Pydantic enforces this at the API layer instead).
CAR_CATEGORIES = ["sedan", "suv", "hatchback", "truck", "van", "convertible", "luxury"]


class Car(Base):
    __tablename__ = "cars"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Foreign key: every car belongs to exactly one owner. This column
    # stores the owning User's id — the actual link, enforced by Postgres
    # itself (an insert with a non-existent owner_id is rejected).
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    # `relationship()` is a SQLAlchemy-only convenience, not a database
    # column — it lets Python code do `car.owner` to get the actual User
    # object (via a query SQLAlchemy generates from owner_id), instead of
    # manually writing `db.query(User).filter(User.id == car.owner_id)`
    # every time you need the owner.
    owner = relationship("User")

    make = Column(String(100), nullable=False)
    model = Column(String(100), nullable=False)
    year = Column(Integer, nullable=False)
    category = Column(String(50), nullable=False, index=True)

    # Location as plain columns, not a separate table: one car has exactly
    # one location — no many-to-many relationship that would justify
    # normalizing this out.
    city = Column(String(100), nullable=False, index=True)
    state = Column(String(100), nullable=True)

    daily_rate = Column(Numeric(10, 2), nullable=False)
    description = Column(Text, nullable=True)

    # Owner-controlled listing toggle — NOT date-based availability (that's
    # the Booking model's job, Phase 5). This just means "currently listed."
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<Car(id={self.id}, make={self.make}, model={self.model}, owner_id={self.owner_id})>"
