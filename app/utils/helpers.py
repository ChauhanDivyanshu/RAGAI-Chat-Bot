"""
Helper Utility Functions
Reusable functions used across the application
"""
import hashlib
import uuid
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List
from app.utils.constants import Patterns, Limits


# ─────────────────────────────────────
# HASHING
# ─────────────────────────────────────

def generate_file_hash(file_bytes: bytes) -> str:
    """Generate SHA-256 hash of file content"""
    return hashlib.sha256(file_bytes).hexdigest()


def generate_content_hash(content: str) -> str:
    """Generate SHA-256 hash of text content"""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def generate_query_hash(query: str, top_k: int = 5) -> str:
    """Generate cache key for query"""
    normalized = query.lower().strip()
    key = f"{normalized}|{top_k}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


# ─────────────────────────────────────
# UUID
# ─────────────────────────────────────

def generate_uuid() -> str:
    """Generate new UUID string"""
    return str(uuid.uuid4())


def is_valid_uuid(value: str) -> bool:
    """Check if string is valid UUID"""
    if not value:
        return False
    return bool(re.match(Patterns.UUID, value.lower()))


def parse_uuid(value: str) -> uuid.UUID:
    """Parse string to UUID, raises ValueError if invalid"""
    return uuid.UUID(value)


# ─────────────────────────────────────
# DATETIME
# ─────────────────────────────────────

def utc_now() -> datetime:
    """Get current UTC datetime"""
    return datetime.now(timezone.utc)


def to_iso_string(dt: Optional[datetime]) -> Optional[str]:
    """Convert datetime to ISO 8601 string"""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


# ─────────────────────────────────────
# STRING UTILITIES
# ─────────────────────────────────────

def sanitize_filename(filename: str) -> str:
    """Sanitize filename to be safe for filesystem"""
    if not filename:
        return "unnamed"
    
    # Remove path components
    filename = Path(filename).name
    
    # Replace unsafe characters
    filename = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', filename)
    
    # Limit length
    if len(filename) > Limits.MAX_FILENAME_LENGTH:
        ext = Path(filename).suffix
        name = Path(filename).stem[:Limits.MAX_FILENAME_LENGTH - len(ext)]
        filename = name + ext
    
    return filename.strip()


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to max length with suffix"""
    if not text or len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def clean_text(text: str) -> str:
    """Basic text cleaning"""
    if not text:
        return ""
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove control characters
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    
    return text.strip()


def word_count(text: str) -> int:
    """Count words in text"""
    if not text:
        return 0
    return len(text.split())


# ─────────────────────────────────────
# FILE UTILITIES
# ─────────────────────────────────────

def get_file_extension(filename: str) -> str:
    """Get file extension in lowercase (without dot)"""
    if not filename:
        return ""
    return Path(filename).suffix.lower().lstrip('.')


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def bytes_to_mb(size_bytes: int) -> float:
    """Convert bytes to MB"""
    return round(size_bytes / (1024 * 1024), 2)


# ─────────────────────────────────────
# VALIDATION
# ─────────────────────────────────────

def validate_query(query: str) -> str:
    """Validate and clean query string"""
    if not query or not query.strip():
        raise ValueError("Query cannot be empty")
    
    cleaned = clean_text(query)
    
    if len(cleaned) < Limits.MIN_QUERY_LENGTH:
        raise ValueError(f"Query too short (min {Limits.MIN_QUERY_LENGTH} characters)")
    
    if len(cleaned) > Limits.MAX_QUERY_LENGTH:
        raise ValueError(f"Query too long (max {Limits.MAX_QUERY_LENGTH} characters)")
    
    return cleaned


def is_safe_filename(filename: str) -> bool:
    """Check if filename is safe"""
    if not filename or len(filename) > Limits.MAX_FILENAME_LENGTH:
        return False
    return bool(re.match(Patterns.SAFE_FILENAME, filename))


# ─────────────────────────────────────
# VECTOR UTILITIES
# ─────────────────────────────────────

def vector_to_pg_string(vector: List[float]) -> str:
    """Convert Python list to PostgreSQL vector string format"""
    return "[" + ",".join(map(str, vector)) + "]"
