from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
import os
from dotenv import load_dotenv
from app.database import get_db
from app.models.user import User
from app.schemas.auth import UserRegister, UserLogin, LoginResponse, UserResponse
from app.utils.security import PasswordHasher, JWTManager, create_user_token_data

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
    Register a new user (regular user or admin)

    - **email**: Must be unique and valid format
    - **password**: Must meet security requirements (8+ chars, uppercase, lowercase, digit)
    - **first_name**: User's first name
    - **last_name**: User's last name
    - **phone**: Optional phone number (required for admins in UI)
    - **is_admin**: Boolean flag to create admin user (from UI form selection)
    """

    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # For admin registration, phone should be provided (UI validation)
    if user_data.is_admin and not user_data.phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number is required for admin accounts",
        )

    # Hash password securely
    hashed_password = PasswordHasher.hash_password(user_data.password)

    # Create new user
    new_user = User(
        email=user_data.email,
        password_hash=hashed_password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        phone=user_data.phone,
        is_admin=user_data.is_admin,
    )

    # Save to database
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Return user data (no sensitive information)
    return UserResponse(
        id=str(new_user.id),
        email=new_user.email,
        first_name=new_user.first_name,
        last_name=new_user.last_name,
        full_name=new_user.full_name,
        phone=new_user.phone,
        is_admin=new_user.is_admin,
        is_active=new_user.is_active,
        created_at=new_user.created_at,
        last_login=new_user.last_login,
    )


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
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            full_name=user.full_name,
            phone=user.phone,
            is_admin=user.is_admin,
            is_active=user.is_active,
            created_at=user.created_at,
            last_login=user.last_login,
        ),
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
            "is_admin": payload.get("is_admin"),
            "expires_at": datetime.fromtimestamp(payload.get("exp")),
            "issued_at": datetime.fromtimestamp(payload.get("iat")),
        }
    except HTTPException:
        return {"valid": False, "message": "Invalid or expired token"}
