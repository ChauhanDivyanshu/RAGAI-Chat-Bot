"""
Request Schemas - All incoming API request models
"""
from typing import Optional, List
from pydantic import BaseModel, Field, validator
from app.utils.constants import Limits


# ─────────────────────────────────────
# EMBEDDING REQUESTS
# ─────────────────────────────────────

class EmbedRequest(BaseModel):
    """Request to generate embedding for text"""
    text: str = Field(..., min_length=1, max_length=10000, description="Text to embed")
    
    @validator('text')
    def text_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Text cannot be empty")
        return v.strip()
    
    class Config:
        json_schema_extra = {
            "example": {"text": "What is artificial intelligence?"}
        }


class SimilarityRequest(BaseModel):
    """Request to compare similarity between two texts"""
    text1: str = Field(..., min_length=1, max_length=10000)
    text2: str = Field(..., min_length=1, max_length=10000)
    
    class Config:
        json_schema_extra = {
            "example": {
                "text1": "What is AI?",
                "text2": "Tell me about artificial intelligence"
            }
        }


# ─────────────────────────────────────
# QUERY REQUESTS (RAG)
# ─────────────────────────────────────

class QueryRequest(BaseModel):
    """Main RAG query request"""
    question: str = Field(
        ...,
        min_length=Limits.MIN_QUERY_LENGTH,
        max_length=Limits.MAX_QUERY_LENGTH,
        description="User question"
    )
    top_k: Optional[int] = Field(
        default=Limits.DEFAULT_TOP_K,
        ge=Limits.MIN_CHUNKS_PER_QUERY,
        le=Limits.MAX_CHUNKS_PER_QUERY,
        description="Number of chunks to retrieve"
    )
    document_id: Optional[str] = Field(
        default=None,
        description="Search only in specific document (UUID)"
    )
    temperature: Optional[float] = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="LLM temperature (0=deterministic, 1=creative)"
    )
    conversation_id: Optional[str] = Field(
        default=None,
        description="Conversation ID for chat history"
    )
    use_cache: Optional[bool] = Field(
        default=True,
        description="Use cached responses if available"
    )
    
    @validator('question')
    def clean_question(cls, v):
        if not v or not v.strip():
            raise ValueError("Question cannot be empty")
        return v.strip()
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "What is RAG and how does it work?",
                "top_k": 5,
                "temperature": 0.3,
                "use_cache": True
            }
        }


class SearchRequest(BaseModel):
    """Search-only request (no LLM generation)"""
    query: str = Field(..., min_length=2, max_length=1000)
    top_k: Optional[int] = Field(default=5, ge=1, le=20)
    document_id: Optional[str] = Field(default=None)
    similarity_threshold: Optional[float] = Field(
        default=0.3,
        ge=0.0,
        le=1.0
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "RAG benefits",
                "top_k": 5,
                "similarity_threshold": 0.3
            }
        }


# ─────────────────────────────────────
# DOCUMENT REQUESTS
# ─────────────────────────────────────

class DocumentListRequest(BaseModel):
    """List documents with filters"""
    status: Optional[str] = Field(default=None, description="Filter by status")
    file_type: Optional[str] = Field(default=None, description="Filter by file type")
    limit: Optional[int] = Field(default=50, ge=1, le=500)
    offset: Optional[int] = Field(default=0, ge=0)


# ─────────────────────────────────────
# USER REQUESTS
# ─────────────────────────────────────

class UserCreateRequest(BaseModel):
    """Create new user"""
    whatsapp_id: str = Field(..., min_length=10, max_length=15)
    name: Optional[str] = Field(default=None, max_length=100)
    role: Optional[str] = Field(default="user")
    
    class Config:
        json_schema_extra = {
            "example": {
                "whatsapp_id": "919876543210",
                "name": "John Doe",
                "role": "user"
            }
        }


# ─────────────────────────────────────
# CONVERSATION REQUESTS
# ─────────────────────────────────────

class ConversationCreateRequest(BaseModel):
    """Start new conversation"""
    user_id: str = Field(..., description="User UUID")
    session_id: Optional[str] = Field(default=None)
