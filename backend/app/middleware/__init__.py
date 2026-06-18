"""
Middleware Package
All FastAPI middleware components
"""
from app.middleware.logging import RequestLoggingMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.error_handler import register_exception_handlers
from app.middleware.cors import setup_cors
from app.middleware.auth import verify_api_key, optional_auth, security


def setup_middleware(app):
    """
    Setup all middleware in correct order.
    
    Order matters! Middleware executes in reverse order of addition:
    - Last added = First executed
    
    Recommended order:
    1. CORS (must be first added = last executed)
    2. Error handlers
    3. Rate limiting
    4. Request logging (last added = first executed)
    """
    # CORS - must be added first
    setup_cors(app)
    
    # Exception handlers
    register_exception_handlers(app)
    
    # Rate limiting
    app.add_middleware(RateLimitMiddleware)
    
    # Request logging (executed first for each request)
    app.add_middleware(RequestLoggingMiddleware)


__all__ = [
    "setup_middleware",
    "RequestLoggingMiddleware",
    "RateLimitMiddleware",
    "register_exception_handlers",
    "setup_cors",
    "verify_api_key",
    "optional_auth",
    "security",
]
