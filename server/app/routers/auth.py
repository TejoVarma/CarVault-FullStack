from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
import os
from dotenv import load_dotenv
from app.database import get_db
from app.models.user import User
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    LoginResponse,
    UserResponse,
    BusinessProfileCreate,
)
from app.utils.security import PasswordHasher, JWTManager, create_user_token_data
from app.utils.auth_deps import get_current_user

# Load environment variables
load_dotenv()

# Get token expiry from environment
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

# Create router instance
router = APIRouter()


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register_user(user_data: UserRegister, db: Session = Depends(get_db)):
    """
    Register a new user (customer or car owner)

    - **email**: Must be unique and valid format
    - **password**: Must meet security requirements (8+ chars, uppercase, lowercase, digit)
    - **first_name**: User's first name
    - **last_name**: User's last name
    - **phone**: Optional for customers, required for car owners
    - **initial_role**: "customer" (default) or "car_owner" — every account is
      always at least a customer; car_owner is an additional role on top
    """

    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # Determine initial roles based on the chosen role at signup
    if user_data.initial_role == "car_owner":
        if not user_data.phone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number is required for car owner accounts",
            )
        initial_roles = ["customer", "car_owner"]
        date_became_car_owner = datetime.utcnow()
    else:
        initial_roles = ["customer"]
        date_became_car_owner = None

    # Hash password securely
    hashed_password = PasswordHasher.hash_password(user_data.password)

    # Create new user
    new_user = User(
        email=user_data.email,
        password_hash=hashed_password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        phone=user_data.phone,
        roles=initial_roles,
        business_verified=False,
        date_became_car_owner=date_became_car_owner,
    )

    # Save to database
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Return user data (no sensitive information); model_validate picks up
    # is_customer/is_car_owner/business_name from the User model's properties
    return UserResponse.model_validate(new_user)


@router.post("/login", response_model=LoginResponse)
async def login_user(credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate user and return JWT token

    - **email**: User's email address
    - **password**: User's password

    Returns access token valid for 24 hours with user information
    """

    # Find user by email
    user = db.query(User).filter(User.email == credentials.email).first()

    # Check if user exists and password is correct
    if not user or not PasswordHasher.verify_password(
        credentials.password, user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user account"
        )

    # Create token data with user information
    token_data = create_user_token_data(user)

    # Generate JWT token (24 hours validity)
    access_token = JWTManager.create_access_token(token_data)

    # Update last login time
    user.last_login = datetime.utcnow()
    db.commit()

    # Return token and user info
    return LoginResponse(
        message="Login successful - valid for 24 hours",
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert minutes to seconds
        user=UserResponse.model_validate(user),
    )


@router.post("/logout")
async def logout_user():
    """
    Logout user (client should discard tokens)

    Note: JWT tokens are stateless, so server-side logout just returns success.
    Client must remove tokens from storage.
    """
    return {
        "message": "Logged out successfully",
        "detail": "Please remove token from client storage",
        "token_validity": "Token will expire automatically in 24 hours",
    }


@router.get("/verify-token")
async def verify_token(token: str):
    """
    Verify if a token is valid (for testing purposes)

    - **token**: JWT token to verify
    """
    try:
        payload = JWTManager.verify_token(token)
        return {
            "valid": True,
            "user_id": payload.get("user_id"),
            "email": payload.get("email"),
            "roles": payload.get("roles"),
            "expires_at": datetime.fromtimestamp(payload.get("exp")),
            "issued_at": datetime.fromtimestamp(payload.get("iat")),
        }
    except HTTPException:
        return {"valid": False, "message": "Invalid or expired token"}


@router.post("/become-car-owner")
async def become_car_owner(
    business_data: BusinessProfileCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upgrade the current (customer) account to also hold the car_owner role.

    - **business_name**, **business_phone**: required
    - **business_description**, **pickup_instructions**: optional
    """
    user = db.query(User).filter(User.id == current_user["id"]).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.has_role("car_owner"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Already a car owner"
        )

    user.add_role("car_owner")
    user.business_profile = {
        "business_info": {
            "business_name": business_data.business_name,
            "business_description": business_data.business_description,
            "business_phone": business_data.business_phone,
        },
        "rental_policies": {
            "pickup_instructions": business_data.pickup_instructions,
        },
    }
    user.date_became_car_owner = datetime.utcnow()
    user.business_verified = False

    db.commit()
    db.refresh(user)

    return {
        "message": "Successfully upgraded to car owner",
        "roles": user.roles,
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get the current authenticated user's full profile, with role info."""
    # current_user (from the dependency) is a fast, partial view built from
    # the JWT + a minimal security-fields query — fetch the full row here
    # since this endpoint's whole purpose is returning the complete profile.
    user = db.query(User).filter(User.id == current_user["id"]).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserResponse.model_validate(user)
