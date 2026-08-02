import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base


class UserPhoto(Base):
    """
    A photo uploaded for a user (currently: profile photos only).

    Separate table rather than just a URL column on User because we also
    need Cloudinary's public_id to manage the asset later (delete/replace
    it) — a bare URL string alone isn't enough to tell Cloudinary which
    asset to remove. This also gives us a natural place to keep photo
    history if that's ever wanted, without changing the User table again.
    """

    __tablename__ = "user_photos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    cloudinary_public_id = Column(String(255), nullable=False, unique=True)
    url = Column(String(500), nullable=False)

    created_at = Column(DateTime, default=func.now(), nullable=False)

    def __repr__(self):
        return f"<UserPhoto(id={self.id}, user_id={self.user_id})>"
