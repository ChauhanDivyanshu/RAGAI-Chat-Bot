"""
Application Constants
Central place for all magic strings, enums, etc.
"""
from enum import Enum


# ─────────────────────────────────────
# FILE TYPES
# ─────────────────────────────────────

class FileType(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    XLSX = "xlsx"
    XLS = "xls"
    CSV = "csv"
    TXT = "txt"
    HTML = "html"
    JPG = "jpg"
    JPEG = "jpeg"
    PNG = "png"


ALLOWED_MIME_TYPES = {
    "application/pdf": FileType.PDF,
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": FileType.DOCX,
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": FileType.XLSX,
    "application/vnd.ms-excel": FileType.XLS,
    "text/csv": FileType.CSV,
    "text/plain": FileType.TXT,
    "text/html": FileType.HTML,
    "image/jpeg": FileType.JPG,
    "image/png": FileType.PNG,
}


# ─────────────────────────────────────
# STATUS ENUMS
# ─────────────────────────────────────

class DocumentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DUPLICATE = "duplicate"


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class QueryComplexity(str, Enum):
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


class ChunkType(str, Enum):
    TEXT = "text"
    TABLE = "table"
    IMAGE = "image"
    CODE = "code"
    HEADING = "heading"


# ─────────────────────────────────────
# MESSAGES
# ─────────────────────────────────────

class Messages:
    # Success
    UPLOAD_SUCCESS = "Document uploaded and processed successfully"
    QUERY_SUCCESS = "Query processed successfully"
    DELETE_SUCCESS = "Document deleted successfully"
    
    # Errors
    FILE_TOO_LARGE = "File size exceeds maximum allowed limit"
    INVALID_FILE_TYPE = "File type not supported"
    DUPLICATE_FILE = "This file has already been uploaded"
    NO_TEXT_EXTRACTED = "Could not extract text from document"
    NO_RELEVANT_CONTEXT = "No relevant information found in uploaded documents"
    DATABASE_ERROR = "Database operation failed"
    LLM_ERROR = "Language model service unavailable"
    EMBEDDING_ERROR = "Failed to generate embeddings"
    
    # Validation
    EMPTY_QUERY = "Query cannot be empty"
    INVALID_DOCUMENT_ID = "Invalid document ID format"


# ─────────────────────────────────────
# LIMITS
# ─────────────────────────────────────

class Limits:
    MAX_QUERY_LENGTH = 1000
    MIN_QUERY_LENGTH = 2
    MAX_CHUNKS_PER_QUERY = 20
    MIN_CHUNKS_PER_QUERY = 1
    MAX_FILENAME_LENGTH = 255
    DEFAULT_TOP_K = 5


# ─────────────────────────────────────
# REGEX PATTERNS
# ─────────────────────────────────────

class Patterns:
    UUID = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    WHATSAPP_ID = r"^\d{10,15}$"
    SAFE_FILENAME = r"^[a-zA-Z0-9._\-\s]+$"
