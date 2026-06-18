"""
Global Error Handler Middleware
Catches all unhandled exceptions and returns standardized error responses
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.utils import logger, RAGException


async def rag_exception_handler(request: Request, exc: RAGException) -> JSONResponse:
    """Handle custom RAG exceptions"""
    request_id = getattr(request.state, 'request_id', 'unknown')
    
    logger.error(
        f"[{request_id}] RAG Exception: {exc.error_code} - {exc.message}"
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.error_code,
            "message": exc.message,
            "details": exc.details,
            "request_id": request_id
        }
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle standard HTTP exceptions"""
    request_id = getattr(request.state, 'request_id', 'unknown')
    
    # Don't log 4xx as errors (they're client errors)
    if exc.status_code >= 500:
        logger.error(f"[{request_id}] HTTP {exc.status_code}: {exc.detail}")
    else:
        logger.warning(f"[{request_id}] HTTP {exc.status_code}: {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": f"HTTP_{exc.status_code}",
            "message": str(exc.detail) if exc.detail else "An error occurred",
            "request_id": request_id
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle Pydantic validation errors"""
    request_id = getattr(request.state, 'request_id', 'unknown')
    
    # Extract validation errors
    errors = []
    for error in exc.errors():
        errors.append({
            "field": " -> ".join(str(loc) for loc in error['loc']),
            "message": error['msg'],
            "type": error['type']
        })
    
    logger.warning(f"[{request_id}] Validation error: {errors}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "details": {"errors": errors},
            "request_id": request_id
        }
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all for unhandled exceptions"""
    request_id = getattr(request.state, 'request_id', 'unknown')
    
    logger.exception(f"[{request_id}] Unhandled exception: {type(exc).__name__} - {str(exc)}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred. Please try again later.",
            "details": {"exception_type": type(exc).__name__},
            "request_id": request_id
        }
    )


def register_exception_handlers(app):
    """Register all exception handlers with FastAPI app"""
    app.add_exception_handler(RAGException, rag_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
