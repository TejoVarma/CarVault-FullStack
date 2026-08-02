from io import BytesIO

import cloudinary.uploader
from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from PIL import Image
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.photo import UserPhoto
from app.schemas.auth import UserProfile, UserProfileUpdate, PasswordChange
from app.utils.auth_deps import get_current_user
from app.utils.security import PasswordHasher

router = APIRouter()

MAX_PHOTO_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
MAX_PHOTO_DIMENSION = 512  # px, longest side after resize
CLOUDINARY_FOLDER = "carvault/profile_photos"


@router.get("/profile", response_model=UserProfile)
def get_profile(
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get the current user's complete profile."""
    user = db.query(User).filter(User.id == current_user["id"]).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserProfile.model_validate(user)


@router.patch("/profile", response_model=UserProfile)
def update_profile(
    profile_data: UserProfileUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update editable profile fields. Only fields included in the request body are changed."""
    user = db.query(User).filter(User.id == current_user["id"]).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # exclude_unset=True: only fields the client actually sent are included —
    # a field explicitly sent as null still updates to null, but an omitted
    # field is left untouched (this is what makes it a partial update).
    updates = profile_data.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return UserProfile.model_validate(user)


@router.put("/change-password")
def change_password(
    password_data: PasswordChange,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Change the current user's password. Requires the current password to verify ownership."""
    user = db.query(User).filter(User.id == current_user["id"]).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if not PasswordHasher.verify_password(password_data.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Current password is incorrect"
        )

    user.password_hash = PasswordHasher.hash_password(password_data.new_password)
    db.commit()
    return {"message": "Password changed successfully"}


@router.post("/profile/photo", response_model=UserProfile)
async def upload_profile_photo(
    file: UploadFile,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload/replace the current user's profile photo. Storage: Cloudinary
    (see plan_docs/design-decisions.md for why). Metadata (Cloudinary's
    public_id + URL) is tracked in the user_photos table, not just a bare
    URL column on User — we need the public_id to delete/replace the
    asset later, which a URL string alone can't give us.

    Security notes (see plan_docs/learning-notes for the full writeup):
    - the client's filename/content-type are never trusted — only Pillow
      actually decoding the bytes as a real image counts
    - the image is re-encoded (not sent to Cloudinary as-is) to strip
      anything hiding in the original file, and resized before upload
    """
    user = db.query(User).filter(User.id == current_user["id"]).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    contents = await file.read()
    if len(contents) > MAX_PHOTO_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Photo must be smaller than {MAX_PHOTO_SIZE_BYTES // (1024 * 1024)}MB",
        )

    try:
        image = Image.open(BytesIO(contents))
        image.verify()  # raises if this isn't actually a valid image
        # Re-open after verify() — verify() leaves the image unusable for
        # further processing, per Pillow's own documented behavior.
        image = Image.open(BytesIO(contents)).convert("RGB")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is not a valid image",
        )

    image.thumbnail((MAX_PHOTO_DIMENSION, MAX_PHOTO_DIMENSION))

    re_encoded = BytesIO()
    image.save(re_encoded, format="JPEG", quality=85)
    re_encoded.seek(0)

    try:
        result = cloudinary.uploader.upload(
            re_encoded,
            folder=CLOUDINARY_FOLDER,
            resource_type="image",
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not upload photo — try again",
        )

    # Replace, don't accumulate: remove the previous photo (Cloudinary asset
    # + its row) before recording the new one.
    existing_photo = db.query(UserPhoto).filter(UserPhoto.user_id == user.id).first()
    if existing_photo:
        try:
            cloudinary.uploader.destroy(existing_photo.cloudinary_public_id)
        except Exception:
            pass  # don't block the new upload over a failed old-asset cleanup
        db.delete(existing_photo)

    new_photo = UserPhoto(
        user_id=user.id,
        cloudinary_public_id=result["public_id"],
        url=result["secure_url"],
    )
    db.add(new_photo)

    user.profile_picture_url = result["secure_url"]
    db.commit()
    db.refresh(user)
    return UserProfile.model_validate(user)
