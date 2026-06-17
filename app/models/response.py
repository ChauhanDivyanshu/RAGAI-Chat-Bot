"""
Response Schemas - All outgoing API response models
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


# ─────────────────────────────────────
# BASE RESPONSES
# ─────────────────────────────────────

class BaseResponse(BaseModel):
    """Base response wrapper"""
    success: bool = True
    message: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standard error response"""
    success: bool = False
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None


# ─────────────────────────────────────
# HEALTH RESPONSES
# ─────────────────────────────────────

class HealthResponse(BaseModel):
    """System health response"""
    status: str
    version: str
    database: str
    ollama: Optional[str] = None
    redis: Optional[str] = None
    timestamp: str


class DBInfoResponse(BaseModel):
    """Database information"""
    tables: List[str]
    extensions: List[str]
    documents_count: int
    chunks_count: int


# ─────────────────────────────────────
# EMBEDDING RESPONSES
# ─────────────────────────────────────

class EmbedResponse(BaseModel):
    """Embedding generation response"""
    text: str
    embedding_dimension: int
    first_5_values: List[float]
    last_5_values: List[float]
    model: str = "BAAI/bge-m3"


class SimilarityResponse(BaseModel):
    """Similarity comparison response"""
    text1: str
    text2: str
    similarity_score: float
    interpretation: str


# ─────────────────────────────────────
# DOCUMENT RESPONSES
# ─────────────────────────────────────

class DocumentInfo(BaseModel):
    """Single document info"""
    id: str
    name: str
    file_type: Optional[str] = None
    size_bytes: int
    size_readable: str
    pages: Optional[int] = None
    chunks: int = 0
    status: str
    language: Optional[str] = None
    uploaded_at: Optional[str] = None
    processed_at: Optional[str] = None


class UploadResponse(BaseModel):
    """Document upload response"""
    success: bool = True
    status: str = Field(..., description="success, duplicate, processing")
    document_id: str
    filename: str
    file_size: int
    file_size_readable: str
    pages: Optional[int] = None
    characters: Optional[int] = None
    chunks_created: int
    chunks_saved: int
    processing_time_ms: Optional[int] = None
    message: str


class DocumentListResponse(BaseModel):
    """List of documents"""
    total: int
    documents: List[DocumentInfo]


class DocumentDeleteResponse(BaseModel):
    """Document deletion response"""
    success: bool = True
    document_id: str
    message: str = "Document deleted successfully"


# ─────────────────────────────────────
# SEARCH RESPONSES
# ─────────────────────────────────────

class ChunkResult(BaseModel):
    """Single chunk in search results"""
    chunk_id: str
    document_id: str
    document_name: str
    content: str
    chunk_index: int
    page_number: Optional[int] = None
    token_count: Optional[int] = None
    similarity_score: float


class SearchResponse(BaseModel):
    """Vector search response"""
    query: str
    total_results: int
    results: List[ChunkResult]
    search_time_ms: int


# ─────────────────────────────────────
# QUERY (RAG) RESPONSES
# ─────────────────────────────────────

class SourceInfo(BaseModel):
    """Source citation in RAG response"""
    document_name: str
    page_number: Optional[int] = None
    chunk_index: Optional[int] = None
    similarity_score: float
    preview: str


class QueryStats(BaseModel):
    """Query processing statistics"""
    chunks_found: int
    model: str
    tokens_used: int = 0
    retrieval_time_ms: int
    llm_time_ms: int
    total_time_ms: int
    cached: bool = False


class QueryResponse(BaseModel):
    """Main RAG query response"""
    success: bool = True
    question: str
    answer: str
    sources: List[SourceInfo]
    stats: QueryStats
    conversation_id: Optional[str] = None


# ─────────────────────────────────────
# LLM TEST RESPONSE
# ─────────────────────────────────────

class OllamaTestResponse(BaseModel):
    """Ollama connectivity test"""
    status: str
    model: str
    response: Optional[str] = None
    error: Optional[str] = None


# ─────────────────────────────────────
# USER RESPONSES
# ─────────────────────────────────────

class UserResponse(BaseModel):
    """User info"""
    id: str
    whatsapp_id: str
    name: Optional[str] = None
    role: str
    created_at: str
    is_active: bool


# ─────────────────────────────────────
# CONVERSATION RESPONSES
# ─────────────────────────────────────

class MessageInfo(BaseModel):
    """Single message in conversation"""
    id: str
    role: str
    content: str
    created_at: str


class ConversationResponse(BaseModel):
    """Conversation info"""
    id: str
    user_id: str
    session_id: Optional[str] = None
    message_count: int
    started_at: str
    messages: Optional[List[MessageInfo]] = None
