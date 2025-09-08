# app/utils/security.py
import os
import bcrypt
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import HTTPException, status
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# JWT Configuration from environment
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fallback-secret-key")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))


class PasswordHasher:
    """Secure password hashing using bcrypt"""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt with salt"""
        # Convert password to bytes
        password_bytes = password.encode("utf-8")

        # Generate salt and hash password
        rounds = int(os.getenv("BCRYPT_ROUNDS", "12"))
        salt = bcrypt.gensalt(rounds=rounds)
        hashed = bcrypt.hashpw(password_bytes, salt)

        # Return as string for database storage
        return hashed.decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        try:
            password_bytes = plain_password.encode("utf-8")
            hashed_bytes = hashed_password.encode("utf-8")
            return bcrypt.checkpw(password_bytes, hashed_bytes)
        except Exception:
            return False


class JWTManager:
    """JWT token creation and validation"""

    @staticmethod
    def create_access_token(
        user_data: dict, expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token with user information (24 hours validity)"""
        to_encode = user_data.copy()

        # Set expiration time
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        # Add expiration and token type to payload
        to_encode.update(
            {
                "exp": expire,
                "iat": datetime.utcnow(),  # Issued at
                "type": "access_token",
            }
        )

        # Create and return JWT token
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    def verify_token(token: str) -> dict:
        """Verify and decode JWT token"""
        try:
            # Decode the token
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

            # Check token type
            token_type = payload.get("type")
            if token_type != "access_token":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type",
                )

            return payload

        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    @staticmethod
    def get_user_from_token(token: str) -> dict:
        """Extract user information from access token"""
        payload = JWTManager.verify_token(token)

        # Extract user information
        user_info = {
            "user_id": payload.get("user_id"),
            "email": payload.get("email"),
            "is_admin": payload.get("is_admin", False),
            "is_active": payload.get("is_active", True),
            "full_name": payload.get("full_name"),
        }

        # Validate required fields
        if not user_info["user_id"] or not user_info["email"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload"
            )

        return user_info


def create_user_token_data(user) -> dict:
    """Create user data payload for JWT token"""
    return {
        "user_id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_admin": user.is_admin,
        "is_active": user.is_active,
        "phone": user.phone,
    }


def validate_password(password: str) -> bool:
    """Validate password strength"""
    if len(password) < 8:
        return False
    if not any(c.isupper() for c in password):
        return False
    if not any(c.islower() for c in password):
        return False
    if not any(c.isdigit() for c in password):
        return False
    return True


def get_password_requirements() -> str:
    """Get password requirements as string"""
    return "Password must be at least 8 characters long and contain uppercase, lowercase, and numeric characters."
