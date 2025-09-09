"""
Authentication Dependencies for Car Rental API

This module provides FastAPI dependencies for route protection with optimized performance:
- JWT validation for speed
- Minimal DB queries for security
- Comprehensive error handling
- Environment-aware responses

Usage Examples:
    @app.get("/profile")
    def get_profile(user: dict = Depends(get_current_user)):
        return user

    @app.get("/admin/dashboard")
    def admin_only(admin: dict = Depends(get_current_admin)):
        return "Admin dashboard"

    @app.get("/cars")
    def browse_cars(user: Optional[dict] = Depends(get_optional_user)):
        # Personalized if logged in, generic if not
"""

import os
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.utils.security import JWTManager

# Security scheme for automatic Swagger/OpenAPI documentation
security = HTTPBearer(
    scheme_name="JWT Bearer Token",
    description="Enter your JWT token from /auth/login endpoint",
    auto_error=False,  # We handle errors manually for better control
)

# Environment check for detailed error messages
DEBUG_MODE = os.getenv("DEBUG", "False").lower() == "true"


def extract_token_from_header(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[str]:
    """
    Extract and validate JWT token from Authorization header

    Args:
        credentials: FastAPI HTTPBearer credentials

    Returns:
        str: Clean JWT token string, None if no credentials

    Raises:
        HTTPException: If token format is invalid
    """
    if not credentials:
        return None

    # Validate token format
    if credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme. Use 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Return clean token
    return credentials.credentials


def get_user_security_info(user_id: str, db: Session) -> Optional[dict]:
    """
    Get security-critical user information from database

    This function performs a minimal query for only security-relevant fields
    to optimize performance while ensuring fresh security status.

    Args:
        user_id: User ID from JWT token
        db: Database session

    Returns:
        dict: Security info (id, is_active, is_admin) or None if user not found
    """
    try:
        # Query only security-critical fields for performance
        user_security = (
            db.query(User.id, User.is_active, User.is_admin)
            .filter(User.id == user_id)
            .first()
        )

        if not user_security:
            return None

        return {
            "id": str(user_security.id),
            "is_active": user_security.is_active,
            "is_admin": user_security.is_admin,
        }
    except Exception:
        # Log error in production, return None for security
        return None


def create_user_response(jwt_payload: dict, security_info: dict) -> dict:
    """
    Combine JWT payload (fast) with fresh security data (secure)

    Args:
        jwt_payload: User data from JWT token
        security_info: Fresh security status from database

    Returns:
        dict: Complete user information for route handlers
    """
    return {
        # Display data from JWT (fast, non-critical)
        "id": jwt_payload.get("user_id"),
        "email": jwt_payload.get("email"),
        "full_name": jwt_payload.get("full_name"),
        "first_name": jwt_payload.get("first_name"),
        "last_name": jwt_payload.get("last_name"),
        "phone": jwt_payload.get("phone"),
        # Security data from DB (fresh, critical)
        "is_active": security_info["is_active"],
        "is_admin": security_info["is_admin"],
        # Metadata
        "auth_method": "jwt_bearer",
        "token_type": "access_token",
    }


async def get_current_user(
    token: Optional[str] = Depends(extract_token_from_header),
    db: Session = Depends(get_db),
) -> dict:
    """
    Get current authenticated user with optimized security checks

    This dependency:
    1. Validates JWT token for authenticity and expiration
    2. Performs minimal DB query for security-critical status
    3. Combines JWT data (fast) with fresh security data (secure)
    4. Ensures account is active and valid

    Args:
        token: JWT token from Authorization header
        db: Database session dependency

    Returns:
        dict: Current user information

    Raises:
        HTTPException: 401 if authentication fails, 403 if account inactive

    Usage:
        @app.get("/profile")
        def get_profile(user: dict = Depends(get_current_user)):
            return f"Hello {user['full_name']}"
    """

    # Check if token is provided
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Validate JWT token and extract payload
        jwt_payload = JWTManager.verify_token(token)
        user_id = jwt_payload.get("user_id")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Get fresh security information from database
        security_info = get_user_security_info(user_id, db)

        if not security_info:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or has been deleted",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check if user account is active
        if not security_info["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account has been deactivated. Contact support for assistance.",
            )

        # Return combined user information
        return create_user_response(jwt_payload, security_info)

    except HTTPException:
        # Re-raise HTTP exceptions (our custom errors)
        raise
    except Exception as e:
        # Handle unexpected errors securely
        error_detail = str(e) if DEBUG_MODE else "Could not validate credentials"
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Get current authenticated admin user

    This dependency builds on get_current_user() and adds admin verification.
    It ensures the user has admin privileges for admin-only routes.

    Args:
        current_user: Current user from get_current_user dependency

    Returns:
        dict: Current admin user information

    Raises:
        HTTPException: 403 if user is not an admin

    Usage:
        @app.post("/cars")
        def add_car(admin: dict = Depends(get_current_admin)):
            return f"Admin {admin['full_name']} can add cars"
    """

    # Verify admin status (using fresh data from get_current_user)
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required for this operation",
        )

    # Add admin-specific metadata
    current_user["role"] = "admin"
    current_user["permissions"] = ["manage_cars", "view_bookings", "manage_inventory"]

    return current_user


async def get_optional_user(
    token: Optional[str] = Depends(extract_token_from_header),
    db: Session = Depends(get_db),
) -> Optional[dict]:
    """
    Get current user if authenticated, None if not authenticated

    This dependency is for routes where authentication is optional but provides
    different functionality for authenticated vs anonymous users.

    Args:
        token: JWT token from Authorization header (optional)
        db: Database session dependency

    Returns:
        dict: Current user info if authenticated, None if anonymous
        Optional[dict]: User data or None

    Raises:
        HTTPException: Only for invalid/expired tokens, not for missing tokens

    Usage:
        @app.get("/cars")
        def browse_cars(user: Optional[dict] = Depends(get_optional_user)):
            if user:
                return f"Personalized cars for {user['full_name']}"
            else:
                return "Generic car listing for anonymous user"
    """

    # If no token provided, return None (anonymous user)
    if not token:
        return None

    try:
        # Use the same logic as get_current_user but don't require authentication
        jwt_payload = JWTManager.verify_token(token)
        user_id = jwt_payload.get("user_id")

        if not user_id:
            return None

        # Get security information
        security_info = get_user_security_info(user_id, db)

        if not security_info or not security_info["is_active"]:
            return None

        # Return user information
        user_data = create_user_response(jwt_payload, security_info)
        user_data["auth_status"] = "authenticated"

        return user_data

    except Exception:
        # For optional auth, invalid tokens return None instead of errors
        # This allows graceful degradation to anonymous mode
        return None


# Dependency aliases for convenience and readability
CurrentUser = Depends(get_current_user)
CurrentAdmin = Depends(get_current_admin)
OptionalUser = Depends(get_optional_user)
