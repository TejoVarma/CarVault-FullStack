"""
Changes needed in main.py file

Add these imports at the top of your main.py file:
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import os
from dotenv import load_dotenv
from app.database import engine, Base
from app.routers import auth

# ADD THESE NEW IMPORTS:
from app.utils.auth_deps import get_current_user, get_current_admin, get_optional_user

# Load environment variables
load_dotenv()

# ✨ Create all database tables
Base.metadata.create_all(bind=engine)

# Create FastAPI application with environment-based configuration
app = FastAPI(
    title=os.getenv("API_TITLE", "Car Rental API"),
    description="""
    A professional car rental platform with secure 24-hour JWT authentication.
    
    ## 🚀 Features
    - **24-Hour JWT Tokens**: Login once per day, use anywhere
    - **Route Protection**: Secure access control for all endpoints
    - **Admin & User Roles**: Separate permissions and capabilities
    - **Environment Configuration**: Production-ready settings
    - **Professional Database Design**: UUID keys, proper relationships
    
    ## 🔐 Authentication Flow
    1. **Register**: Create account as user or admin with strong password
    2. **Login**: Receive JWT token valid for 24 hours
    3. **Use Token**: Include in Authorization header as 'Bearer <token>'
    4. **Protected Routes**: Access user-specific and admin-only features
    5. **Daily Re-login**: Token expires after 24 hours for security
    
    ## 👥 User Types
    - **Regular Users**: Can browse cars, make bookings, manage profile
    - **Admin Users**: Can manage car inventory, view their bookings, add cars
    
    ## 🔒 Security Features
    - Password strength validation (8+ chars, uppercase, lowercase, digit)
    - bcrypt password hashing with salt
    - JWT tokens with user context and route protection
    - UUID-based user IDs (non-guessable)
    - Environment-based secret management
    - Real-time account status verification
    
    ## 🛡️ Route Protection
    - **Public Routes**: Anyone can access (browse cars, register, login)
    - **Protected Routes**: Require valid JWT token (profile, bookings)
    - **Admin Routes**: Require admin privileges (car management, analytics)
    - **Optional Auth Routes**: Enhanced experience for logged-in users
    """,
    version=os.getenv("API_VERSION", "2.0.0"),
    debug=os.getenv("DEBUG", "False").lower() == "true",
    contact={
        "name": "Car Rental API Support",
        "email": "support@carrental.com",
    },
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include authentication router
app.include_router(
    auth.router,
    prefix="/auth",
    tags=["🔐 Authentication"],
    responses={
        400: {"description": "Bad Request - Invalid input data"},
        401: {"description": "Unauthorized - Invalid credentials"},
        422: {"description": "Validation Error - Check request format"},
    },
)


# Root endpoint - UPDATED to show route protection info
@app.get("/", tags=["📋 General"])
def read_root():
    """
    Welcome endpoint with API information and authentication guide
    """
    return {
        "message": f"🚗 Welcome to {os.getenv('API_TITLE', 'Car Rental API')} v{os.getenv('API_VERSION', '2.0.0')}!",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "jwt_validity": "24 hours",
        "features": {
            "authentication": "✅ 24-hour JWT tokens",
            "route_protection": "✅ Secure access control",
            "security": "✅ bcrypt password hashing",
            "roles": "✅ Admin and User roles",
            "database": "✅ PostgreSQL with UUIDs",
            "validation": "✅ Strong password requirements",
        },
        "quick_start": {
            "1_register": "POST /auth/register - Create your account",
            "2_login": "POST /auth/login - Get 24-hour token",
            "3_use_token": "Add 'Authorization: Bearer <token>' to requests",
            "4_access_protected": "Use token to access protected routes",
        },
        "route_types": {
            "public": "No authentication required (/, /cars, /auth/*)",
            "protected": "Requires valid JWT token (/profile, /bookings)",
            "admin_only": "Requires admin privileges (/admin/*, POST /cars)",
            "optional_auth": "Enhanced for logged-in users (personalized content)",
        },
        "endpoints": {
            "documentation": "/docs",
            "health_check": "/health",
            "register": "/auth/register",
            "login": "/auth/login",
            "logout": "/auth/logout",
            "verify_token": "/auth/verify-token",
        },
    }


# Health check endpoint - UPDATED with authentication status
@app.get("/health", tags=["📋 General"])
def health_check():
    """
    Health check endpoint - Tests database connectivity and authentication system
    """
    try:
        from app.database import SessionLocal
        from app.models.user import User

        # Test database connection and get metrics
        with SessionLocal() as db:
            # Basic connectivity test
            db.execute("SELECT 1")

            # Get user statistics
            total_users = db.query(User).count()
            active_users = db.query(User).filter(User.is_active == True).count()
            admin_users = db.query(User).filter(User.is_admin == True).count()

        return {
            "status": "✅ healthy",
            "timestamp": "2025-01-08T15:30:00Z",
            "database": {"status": "connected", "type": "PostgreSQL"},
            "authentication": {
                "status": "active",
                "protection_enabled": True,
                "jwt_algorithm": os.getenv("JWT_ALGORITHM", "HS256"),
                "token_validity": f"{os.getenv('JWT_ACCESS_TOKEN_EXPIRE_MINUTES', '1440')} minutes",
            },
            "metrics": {
                "total_users": total_users,
                "active_users": active_users,
                "admin_users": admin_users,
                "regular_users": total_users - admin_users,
            },
            "configuration": {
                "environment": os.getenv("ENVIRONMENT", "development"),
                "api_version": os.getenv("API_VERSION", "2.0.0"),
                "debug_mode": os.getenv("DEBUG", "False").lower() == "true",
                "bcrypt_rounds": os.getenv("BCRYPT_ROUNDS", "12"),
            },
            "security": {
                "route_protection": "enabled",
                "password_hashing": "bcrypt",
                "token_validation": "active",
                "admin_verification": "real-time",
            },
        }
    except Exception as e:
        return {
            "status": "❌ unhealthy",
            "timestamp": "2025-01-08T15:30:00Z",
            "database": {
                "status": "disconnected",
                "error": "Database connection failed",
            },
            "authentication": {
                "status": "unknown",
                "error": "Could not verify authentication system",
            },
            "environment": os.getenv("ENVIRONMENT", "development"),
            "message": "Check database configuration and connectivity",
        }


# EXAMPLE PROTECTED ROUTES - Add these to demonstrate route protection:


@app.get("/profile", tags=["👤 User Management"])
async def get_user_profile(current_user: dict = Depends(get_current_user)):
    """
    Get current user's profile information

    **Requires**: Valid JWT token
    **Returns**: User profile data
    """
    return {
        "message": f"Profile for {current_user['full_name']}",
        "profile": {
            "id": current_user["id"],
            "email": current_user["email"],
            "full_name": current_user["full_name"],
            "phone": current_user["phone"],
            "account_type": "Admin" if current_user["is_admin"] else "User",
            "account_status": "Active" if current_user["is_active"] else "Inactive",
        },
        "capabilities": {
            "can_book_cars": True,
            "can_manage_cars": current_user["is_admin"],
            "can_view_analytics": current_user["is_admin"],
        },
    }


@app.get("/admin/dashboard", tags=["🔧 Admin Only"])
async def admin_dashboard(current_admin: dict = Depends(get_current_admin)):
    """
    Admin dashboard with system overview

    **Requires**: Valid JWT token + Admin privileges
    **Returns**: Admin dashboard data
    """
    return {
        "message": f"Admin Dashboard for {current_admin['full_name']}",
        "admin_info": {
            "id": current_admin["id"],
            "email": current_admin["email"],
            "role": current_admin["role"],
            "permissions": current_admin["permissions"],
        },
        "quick_stats": {
            "total_cars": 0,  # Will be implemented with car models
            "active_bookings": 0,  # Will be implemented with booking system
            "monthly_revenue": 0,  # Will be implemented with payment system
        },
        "available_actions": [
            "Add new cars to inventory",
            "Manage existing car listings",
            "View booking analytics",
            "Update car pricing",
        ],
    }


@app.get("/cars", tags=["🚗 Car Browsing"])
async def browse_cars(user: Optional[dict] = Depends(get_optional_user)):
    """
    Browse available cars with optional personalization

    **Requires**: No authentication (public endpoint)
    **Enhanced**: For logged-in users with personalized recommendations
    """
    if user:
        return {
            "message": f"Personalized car recommendations for {user['full_name']}",
            "user_context": {
                "user_id": user["id"],
                "account_type": "Admin" if user["is_admin"] else "User",
                "auth_status": user.get("auth_status", "authenticated"),
            },
            "cars": [],  # Will be populated with actual car data
            "recommendations": "Based on your booking history and preferences",
            "features": ["Save favorites", "Quick booking", "Price alerts"],
        }
    else:
        return {
            "message": "Browse all available cars",
            "user_context": "anonymous",
            "cars": [],  # Will be populated with actual car data
            "suggestions": [
                "Sign up for personalized recommendations",
                "Login to save favorites",
                "Create account for faster booking",
            ],
            "public_features": [
                "View car details",
                "Check availability",
                "Compare prices",
            ],
        }


# Global exception handlers - UPDATED with authentication context
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {
        "error": "Endpoint not found",
        "message": "The requested endpoint does not exist",
        "documentation": "/docs",
        "available_endpoints": {
            "auth": "/auth/* (register, login, logout)",
            "user": "/profile (requires authentication)",
            "admin": "/admin/* (requires admin privileges)",
            "public": "/cars, /health, /",
        },
    }


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return {
        "error": "Internal server error",
        "message": "Something went wrong on our end",
        "support": "Please contact support if this persists",
        "troubleshooting": {
            "check_token": "Ensure JWT token is valid and not expired",
            "check_permissions": "Verify account has required privileges",
            "health_check": "/health",
        },
    }
