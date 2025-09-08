# app/main.py - Complete FastAPI App with 24-hour JWT Authentication
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from app.database import engine, Base
from app.routers import auth

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
    - **Secure Password Hashing**: bcrypt with configurable rounds
    - **Admin & User Roles**: Separate permissions and capabilities
    - **Environment Configuration**: Production-ready settings
    - **Professional Database Design**: UUID keys, proper relationships
    
    ## 🔐 Authentication Flow
    1. **Register**: Create account as user or admin with strong password
    2. **Login**: Receive JWT token valid for 24 hours
    3. **Use Token**: Include in Authorization header as 'Bearer <token>'
    4. **Daily Re-login**: Token expires after 24 hours for security
    
    ## 👥 User Types
    - **Regular Users**: Can browse and rent cars, manage their bookings
    - **Admin Users**: Can manage car inventory, view all bookings, user management
    
    ## 🔒 Security Features
    - Password strength validation (8+ chars, uppercase, lowercase, digit)
    - bcrypt password hashing with salt
    - JWT tokens with user context
    - UUID-based user IDs (non-guessable)
    - Environment-based secret management
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


# Root endpoint
@app.get("/", tags=["📋 General"])
def read_root():
    """
    Welcome endpoint with API information and quick start guide
    """
    return {
        "message": f"🚗 Welcome to {os.getenv('API_TITLE', 'Car Rental API')} v{os.getenv('API_VERSION', '2.0.0')}!",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "jwt_validity": "24 hours",
        "features": {
            "authentication": "✅ 24-hour JWT tokens",
            "security": "✅ bcrypt password hashing",
            "roles": "✅ Admin and User roles",
            "database": "✅ PostgreSQL with UUIDs",
            "validation": "✅ Strong password requirements",
        },
        "quick_start": {
            "1_register": "POST /auth/register - Create your account",
            "2_login": "POST /auth/login - Get 24-hour token",
            "3_use_token": "Add 'Authorization: Bearer <token>' to requests",
        },
        "endpoints": {
            "documentation": "/docs",
            "health_check": "/health",
            "register": "/auth/register",
            "login": "/auth/login",
            "logout": "/auth/logout",
        },
    }


# Health check endpoint with database connectivity test
@app.get("/health", tags=["📋 General"])
def health_check():
    """
    Health check endpoint - Tests database connectivity and system status
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
            "metrics": {
                "total_users": total_users,
                "active_users": active_users,
                "admin_users": admin_users,
                "regular_users": total_users - admin_users,
            },
            "configuration": {
                "environment": os.getenv("ENVIRONMENT", "development"),
                "api_version": os.getenv("API_VERSION", "2.0.0"),
                "jwt_expiry": f"{os.getenv('JWT_ACCESS_TOKEN_EXPIRE_MINUTES', '1440')} minutes",
                "bcrypt_rounds": os.getenv("BCRYPT_ROUNDS", "12"),
            },
            "security": {
                "jwt_algorithm": os.getenv("JWT_ALGORITHM", "HS256"),
                "password_hashing": "bcrypt",
                "token_validity": "24 hours",
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
            "environment": os.getenv("ENVIRONMENT", "development"),
            "message": "Check database configuration and connectivity",
        }


# Global exception handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {
        "error": "Endpoint not found",
        "message": "The requested endpoint does not exist",
        "documentation": "/docs",
        "available_endpoints": {"auth": "/auth/*", "health": "/health", "root": "/"},
    }


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return {
        "error": "Internal server error",
        "message": "Something went wrong on our end",
        "support": "Please contact support if this persists",
        "health_check": "/health",
    }
