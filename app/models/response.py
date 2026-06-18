"""
Response Schemas
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class BaseResponse(BaseModel):
    success: bool = True
    message: Optional[str] = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    status: str
    version: str
    database: str
    ollama: Optional[str] = None
    redis: Optional[str] = None
    timestamp: str


class DBInfoResponse(BaseModel):
    tables: List[str]
    extensions: List[str]
    documents_count: int
    chunks_count: int


class EmbedResponse(BaseModel):
    text: str
    embedding_dimension: int
    first_5_values: List[float]
    last_5_values: List[float]
    model: str = "BAAI/bge-m3"


class SimilarityResponse(BaseModel):
    text1: str
    text2: str
    similarity_score: float
    interpretation: str


class DocumentInfo(BaseModel):
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
    success: bool = True
    status: str
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
    total: int
    documents: List[DocumentInfo]


class DocumentDeleteResponse(BaseModel):
    success: bool = True
    document_id: str
    message: str = "Document deleted successfully"


class ChunkResult(BaseModel):
    chunk_id: str
    document_id: str
    document_name: str
    content: str
    chunk_index: int
    page_number: Optional[int] = None
    token_count: Optional[int] = None
    similarity_score: float


class SearchResponse(BaseModel):
    query: str
    total_results: int
    results: List[ChunkResult]
    search_time_ms: int


class SourceInfo(BaseModel):
    document_name: str
    page_number: Optional[int] = None
    chunk_index: Optional[int] = None
    similarity_score: float
    preview: str


class QueryStats(BaseModel):
    chunks_found: int
    model: str
    tokens_used: int = 0
    retrieval_time_ms: int
    llm_time_ms: int
    total_time_ms: int
    cached: bool = False
    detected_language: Optional[str] = "english"


class QueryResponse(BaseModel):
    success: bool = True
    question: str
    answer: str
    sources: List[SourceInfo]
    stats: QueryStats
    conversation_id: Optional[str] = None


class OllamaTestResponse(BaseModel):
    status: str
    model: str
    response: Optional[str] = None
    error: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    whatsapp_id: str
    name: Optional[str] = None
    role: str
    created_at: str
    is_active: bool


class MessageInfo(BaseModel):
    id: str
    role: str
    content: str
    created_at: str


class ConversationResponse(BaseModel):
    id: str
    user_id: str
    session_id: Optional[str] = None
    message_count: int
    started_at: str
    messages: Optional[List[MessageInfo]] = None
