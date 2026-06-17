"""
Rate Limiting Middleware
Simple in-memory rate limiting (Redis-based can be added later)
"""
import time
from collections import defaultdict
from typing import Dict, Tuple
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.utils import logger
from app.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple rate limiting per IP address.
    
    Limits:
    - General: 60 requests per minute
    - Upload: 10 requests per hour
    """
    
    def __init__(self, app):
        super().__init__(app)
        # Storage: {ip: [(timestamp, endpoint), ...]}
        self.requests: Dict[str, list] = defaultdict(list)
        
        # Rate limits per endpoint pattern
        self.limits = {
            "/upload": (settings.UPLOAD_RATE_LIMIT, 3600),  # 10/hour
            "default": (settings.QUERY_RATE_LIMIT, 60),     # 60/minute
        }
    
    def _get_limit(self, path: str) -> Tuple[int, int]:
        """Get rate limit for a path (max_requests, window_seconds)"""
        for prefix, limit in self.limits.items():
            if prefix != "default" and path.startswith(prefix):
                return limit
        return self.limits["default"]
    
    def _cleanup_old_requests(self, ip: str, window_seconds: int):
        """Remove old requests outside the window"""
        cutoff = time.time() - window_seconds
        self.requests[ip] = [
            (ts, ep) for ts, ep in self.requests[ip] if ts > cutoff
        ]
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks and docs
        path = request.url.path
        if path in ("/health", "/", "/docs", "/openapi.json", "/redoc"):
            return await call_next(request)
        
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Get rate limit for this endpoint
        max_requests, window_seconds = self._get_limit(path)
        
        # Cleanup old requests
        self._cleanup_old_requests(client_ip, window_seconds)
        
        # Count requests in window
        current_count = len(self.requests[client_ip])
        
        # Check limit
        if current_count >= max_requests:
            logger.warning(
                f"Rate limit exceeded for {client_ip} on {path} "
                f"({current_count}/{max_requests} in {window_seconds}s)"
            )
            
            window_text = "minute" if window_seconds == 60 else "hour"
            
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "RATE_LIMIT_EXCEEDED",
                    "message": f"Rate limit exceeded: {max_requests} requests per {window_text}",
                    "details": {
                        "limit": max_requests,
                        "window_seconds": window_seconds,
                        "retry_after": window_seconds
                    }
                },
                headers={
                    "Retry-After": str(window_seconds),
                    "X-RateLimit-Limit": str(max_requests),
                    "X-RateLimit-Remaining": "0"
                }
            )
        
        # Record this request
        self.requests[client_ip].append((time.time(), path))
        
        # Add rate limit headers
        response = await call_next(request)
        remaining = max_requests - current_count - 1
        response.headers["X-RateLimit-Limit"] = str(max_requests)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        
        return response
