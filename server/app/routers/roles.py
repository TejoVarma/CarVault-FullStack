from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from app.database import get_db
from app.models.user import User
from app.schemas.auth import BusinessProfileUpdate, CustomerProfileUpdate
from app.utils.auth_deps import get_current_customer, get_current_car_owner

router = APIRouter()


@router.patch("/customer-profile")
def update_customer_profile(
    profile_data: CustomerProfileUpdate,
    current_customer: dict = Depends(get_current_customer),
    db: Session = Depends(get_db),
):
    """Update the current user's customer preferences."""
    user = db.query(User).filter(User.id == current_customer["id"]).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if not user.customer_profile:
        user.customer_profile = {}

    if profile_data.rental_preferences is not None:
        user.customer_profile["rental_preferences"] = profile_data.rental_preferences
    if profile_data.communication_preferences is not None:
        user.customer_profile["communication_preferences"] = profile_data.communication_preferences

    # SQLAlchemy doesn't detect in-place mutation of a JSONB column's dict
    # (it only tracks reassignment of the attribute itself) — flag_modified
    # tells it explicitly that this column needs to be included in the UPDATE.
    flag_modified(user, "customer_profile")
    db.commit()
    return {"message": "Customer profile updated"}


@router.patch("/business-profile")
def update_business_profile(
    profile_data: BusinessProfileUpdate,
    current_car_owner: dict = Depends(get_current_car_owner),
    db: Session = Depends(get_db),
):
    """Update the current user's business profile (car owners only)."""
    user = db.query(User).filter(User.id == current_car_owner["id"]).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if not user.business_profile:
        user.business_profile = {"business_info": {}}

    business_info = user.business_profile.get("business_info", {})
    if profile_data.business_name is not None:
        business_info["business_name"] = profile_data.business_name
    if profile_data.business_description is not None:
        business_info["business_description"] = profile_data.business_description
    if profile_data.business_phone is not None:
        business_info["business_phone"] = profile_data.business_phone
    if profile_data.pickup_instructions is not None:
        rental_policies = user.business_profile.get("rental_policies", {})
        rental_policies["pickup_instructions"] = profile_data.pickup_instructions
        user.business_profile["rental_policies"] = rental_policies

    user.business_profile["business_info"] = business_info

    flag_modified(user, "business_profile")
    db.commit()
    return {"message": "Business profile updated"}
