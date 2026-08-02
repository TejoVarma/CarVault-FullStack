from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.auth import UserProfile, UserProfileUpdate, PasswordChange
from app.utils.auth_deps import get_current_user
from app.utils.security import PasswordHasher

router = APIRouter()


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
