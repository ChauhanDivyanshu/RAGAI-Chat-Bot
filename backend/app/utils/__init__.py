"""Utils package - shared utility functions"""
from app.utils.logger import logger
from app.utils.constants import (
    FileType, DocumentStatus, TaskStatus,
    MessageRole, QueryComplexity, ChunkType,
    Messages, Limits, Patterns, ALLOWED_MIME_TYPES
)
from app.utils.exceptions import (
    RAGException, ValidationError, NotFoundError,
    FileTooLargeError, InvalidFileTypeError, DuplicateError,
    RateLimitError, AuthenticationError,
    DatabaseError, LLMServiceError, EmbeddingError,
    DocumentProcessingError, ExtractionError
)
from app.utils.helpers import (
    generate_file_hash, generate_content_hash, generate_query_hash,
    generate_uuid, is_valid_uuid, parse_uuid,
    utc_now, to_iso_string,
    sanitize_filename, truncate_text, clean_text, word_count,
    get_file_extension, format_file_size, bytes_to_mb,
    validate_query, is_safe_filename,
    vector_to_pg_string
)

__all__ = [
    # Logger
    "logger",
    # Constants
    "FileType", "DocumentStatus", "TaskStatus",
    "MessageRole", "QueryComplexity", "ChunkType",
    "Messages", "Limits", "Patterns", "ALLOWED_MIME_TYPES",
    # Exceptions
    "RAGException", "ValidationError", "NotFoundError",
    "FileTooLargeError", "InvalidFileTypeError", "DuplicateError",
    "RateLimitError", "AuthenticationError",
    "DatabaseError", "LLMServiceError", "EmbeddingError",
    "DocumentProcessingError", "ExtractionError",
    # Helpers
    "generate_file_hash", "generate_content_hash", "generate_query_hash",
    "generate_uuid", "is_valid_uuid", "parse_uuid",
    "utc_now", "to_iso_string",
    "sanitize_filename", "truncate_text", "clean_text", "word_count",
    "get_file_extension", "format_file_size", "bytes_to_mb",
    "validate_query", "is_safe_filename",
    "vector_to_pg_string"
]
