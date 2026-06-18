"""
Request/Response Logging Middleware
Logs every API request with timing
"""
import time
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.utils import logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all incoming requests and responses with timing"""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Generate request ID for tracing
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id
        
        # Log incoming request
        start_time = time.time()
        client_ip = request.client.host if request.client else "unknown"
        
        logger.info(
            f"[{request_id}] -> {request.method} {request.url.path} "
            f"from {client_ip}"
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Add custom headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time-Ms"] = str(duration_ms)
            
            # Log response
            status_emoji = "OK" if response.status_code < 400 else "ERR"
            logger.info(
                f"[{request_id}] <- {response.status_code} [{status_emoji}] "
                f"in {duration_ms}ms"
            )
            
            return response
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(
                f"[{request_id}] <- EXCEPTION in {duration_ms}ms: {str(e)}"
            )
            raise
