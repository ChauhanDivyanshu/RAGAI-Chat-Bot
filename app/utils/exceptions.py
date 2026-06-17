"""
Custom Exception Classes
Provides structured error handling
"""
from typing import Optional, Dict, Any
from fastapi import HTTPException, status


class RAGException(Exception):
    """Base exception for RAG system"""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_http_exception(self) -> HTTPException:
        return HTTPException(
            status_code=self.status_code,
            detail={
                "error": self.error_code,
                "message": self.message,
                "details": self.details
            }
        )


# ─────────────────────────────────────
# CLIENT ERRORS (4xx)
# ─────────────────────────────────────

class ValidationError(RAGException):
    """Input validation failed"""
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR",
            details=details
        )


class NotFoundError(RAGException):
    """Resource not found"""
    def __init__(self, resource: str, identifier: str = ""):
        super().__init__(
            message=f"{resource} not found" + (f": {identifier}" if identifier else ""),
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="NOT_FOUND",
            details={"resource": resource, "identifier": identifier}
        )


class FileTooLargeError(RAGException):
    """File exceeds size limit"""
    def __init__(self, file_size: int, max_size: int):
        super().__init__(
            message=f"File size {file_size} bytes exceeds limit of {max_size} bytes",
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            error_code="FILE_TOO_LARGE",
            details={"file_size": file_size, "max_size": max_size}
        )


class InvalidFileTypeError(RAGException):
    """Unsupported file type"""
    def __init__(self, file_type: str, allowed_types: list):
        super().__init__(
            message=f"File type '{file_type}' not supported",
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="INVALID_FILE_TYPE",
            details={"received": file_type, "allowed": allowed_types}
        )


class DuplicateError(RAGException):
    """Duplicate resource"""
    def __init__(self, resource: str, identifier: str):
        super().__init__(
            message=f"{resource} already exists",
            status_code=status.HTTP_409_CONFLICT,
            error_code="DUPLICATE_RESOURCE",
            details={"resource": resource, "identifier": identifier}
        )


class RateLimitError(RAGException):
    """Rate limit exceeded"""
    def __init__(self, limit: int, window: str):
        super().__init__(
            message=f"Rate limit exceeded: {limit} requests per {window}",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code="RATE_LIMIT_EXCEEDED",
            details={"limit": limit, "window": window}
        )


class AuthenticationError(RAGException):
    """Authentication failed"""
    def __init__(self, message: str = "Invalid or missing API key"):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="AUTHENTICATION_FAILED"
        )


# ─────────────────────────────────────
# SERVER ERRORS (5xx)
# ─────────────────────────────────────

class DatabaseError(RAGException):
    """Database operation failed"""
    def __init__(self, message: str = "Database operation failed", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="DATABASE_ERROR",
            details=details
        )


class LLMServiceError(RAGException):
    """LLM service error"""
    def __init__(self, message: str = "LLM service unavailable"):
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="LLM_SERVICE_ERROR"
        )


class EmbeddingError(RAGException):
    """Embedding generation failed"""
    def __init__(self, message: str = "Failed to generate embeddings"):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="EMBEDDING_ERROR"
        )


class DocumentProcessingError(RAGException):
    """Document processing failed"""
    def __init__(self, message: str, stage: str = "unknown"):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="DOCUMENT_PROCESSING_ERROR",
            details={"stage": stage}
        )


class ExtractionError(RAGException):
    """Text extraction failed"""
    def __init__(self, file_type: str, reason: str = ""):
        super().__init__(
            message=f"Failed to extract text from {file_type} file" + (f": {reason}" if reason else ""),
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="EXTRACTION_ERROR",
            details={"file_type": file_type, "reason": reason}
        )
