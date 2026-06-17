"""Models package - Pydantic schemas for API"""

from app.models.request import (
    EmbedRequest,
    SimilarityRequest,
    QueryRequest,
    SearchRequest,
    DocumentListRequest,
    UserCreateRequest,
    ConversationCreateRequest,
)

from app.models.response import (
    # Base
    BaseResponse,
    ErrorResponse,
    # Health
    HealthResponse,
    DBInfoResponse,
    # Embeddings
    EmbedResponse,
    SimilarityResponse,
    # Documents
    DocumentInfo,
    UploadResponse,
    DocumentListResponse,
    DocumentDeleteResponse,
    # Search
    ChunkResult,
    SearchResponse,
    # Query (RAG)
    SourceInfo,
    QueryStats,
    QueryResponse,
    # Ollama
    OllamaTestResponse,
    # User
    UserResponse,
    # Conversation
    MessageInfo,
    ConversationResponse,
)

__all__ = [
    # Requests
    "EmbedRequest", "SimilarityRequest", "QueryRequest", "SearchRequest",
    "DocumentListRequest", "UserCreateRequest", "ConversationCreateRequest",
    # Responses - Base
    "BaseResponse", "ErrorResponse",
    # Responses - Health
    "HealthResponse", "DBInfoResponse",
    # Responses - Embeddings
    "EmbedResponse", "SimilarityResponse",
    # Responses - Documents
    "DocumentInfo", "UploadResponse", "DocumentListResponse", "DocumentDeleteResponse",
    # Responses - Search
    "ChunkResult", "SearchResponse",
    # Responses - Query
    "SourceInfo", "QueryStats", "QueryResponse",
    # Responses - Ollama
    "OllamaTestResponse",
    # Responses - User
    "UserResponse",
    # Responses - Conversation
    "MessageInfo", "ConversationResponse",
]
