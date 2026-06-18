"""
CORS Middleware Configuration
"""
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings


def setup_cors(app):
    """Configure CORS for the application"""
    
    # In development: allow all origins
    # In production: restrict to specific domains
    if settings.ENVIRONMENT == "development":
        allowed_origins = ["*"]
    else:
        # Add your frontend URLs here in production
        allowed_origins = [
            "https://yourdomain.com",
            "https://app.yourdomain.com",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:8001",
        ]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=[
            "X-Request-ID",
            "X-Process-Time-Ms",
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining"
        ]
    )
