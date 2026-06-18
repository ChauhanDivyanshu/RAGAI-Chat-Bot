"""
Authentication Middleware (Basic API Key)
Can be enhanced with JWT later
"""
from typing import Optional
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends

from app.config import settings
from app.utils import logger, AuthenticationError


# Security scheme for Swagger UI
security = HTTPBearer(auto_error=False)


async def verify_api_key(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> bool:
    """
    Verify API key (optional dependency).
    
    In development: No auth required
    In production: Bearer token required
    
    Usage in endpoints:
        @router.post("/protected", dependencies=[Depends(verify_api_key)])
    """
    # Skip auth in development
    if settings.ENVIRONMENT == "development":
        return True
    
    # Production: require valid API key
    if not credentials:
        raise AuthenticationError("Missing API key").to_http_exception()
    
    # TODO: Implement proper key validation (database lookup, JWT, etc.)
    # For now, simple check
    if credentials.credentials != settings.SECRET_KEY:
        logger.warning(f"Invalid API key attempt")
        raise AuthenticationError("Invalid API key").to_http_exception()
    
    return True


async def optional_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[str]:
    """
    Optional authentication - returns user info if authenticated.
    Used for endpoints that work for both anonymous and authenticated users.
    """
    if not credentials:
        return None
    
    # TODO: Validate and return user info
    return "anonymous"
