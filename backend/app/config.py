from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # App
    APP_NAME: str = "RAG System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    SECRET_KEY: str

    # Database
    DATABASE_URL: str
    DB_MIN_CONNECTIONS: int = 5
    DB_MAX_CONNECTIONS: int = 20

    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_CACHE_DB: int = 0
    REDIS_CELERY_DB: int = 1
    REDIS_RATE_LIMIT_DB: int = 2
    REDIS_SESSION_DB: int = 3
    REDIS_PROGRESS_DB: int = 4
    REDIS_PASSWORD_DB: int = 5

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # WhatsApp
    WHATSAPP_TOKEN: str = ""
    WHATSAPP_PHONE_ID: str = ""
    WHATSAPP_APP_SECRET: str = ""
    WHATSAPP_VERIFY_TOKEN: str = ""
    WHATSAPP_API_VERSION: str = "v18.0"

    # Cloudflare R2
    CF_ACCOUNT_ID: str = ""
    CLOUDFLARE_R2_ACCESS_KEY: str = ""
    CLOUDFLARE_R2_SECRET_KEY: str = ""
    CLOUDFLARE_R2_BUCKET: str = "rag-documents"
    CLOUDFLARE_R2_PUBLIC_URL: str = ""

    # ═══════════════════════════════════════════
    # 🤖 OLLAMA - UPGRADED MODELS
    # ═══════════════════════════════════════════
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    
    # 🔥 BEST for Hindi + English + Hinglish (8B params)
    OLLAMA_MAIN_MODEL: str = "llama3.2:3b"
    
    # Backup judge model
    OLLAMA_JUDGE_MODEL: str = "llama3.1:8b"
    
    OLLAMA_TIMEOUT: int = 120

    # Add in Settings class:
    TAVILY_API_KEY: str = ""
    USE_TAVILY: bool = True

    # ⚡ GROQ Configuration
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    USE_GROQ: bool = False

    # ML Models
    EMBEDDING_MODEL: str = "BAAI/bge-m3"
    RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    MODELS_CACHE_DIR: str = "./models_cache"
    EMBEDDING_BATCH_SIZE: int = 32
    EMBEDDING_CACHE_TTL: int = 604800

    # Paid APIs
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "us-east-1"
    GOOGLE_CREDENTIALS_PATH: str = "./google-credentials.json"
    LLAMAPARSE_API_KEY: str = ""

    # Rate Limits
    UPLOAD_RATE_LIMIT: int = 10
    QUERY_RATE_LIMIT: int = 60
    MAX_CONCURRENT_UPLOADS: int = 5

    # File Limits
    MAX_PDF_SIZE: int = 52428800
    MAX_DOCX_SIZE: int = 26214400
    MAX_EXCEL_SIZE: int = 20971520
    MAX_IMAGE_SIZE: int = 20971520
    MAX_CSV_SIZE: int = 52428800

    # ═══════════════════════════════════════════
    # 📝 CHUNKING - OPTIMIZED
    # ═══════════════════════════════════════════
    CHUNK_SIZE: int = 512          # Sweet spot for BGE-M3
    CHUNK_OVERLAP: int = 128       # 25% overlap (better context preservation)

    # ═══════════════════════════════════════════
    # 🎯 RETRIEVAL - TUNED FOR ACCURACY
    # ═══════════════════════════════════════════
    RETRIEVAL_TOP_K_SIMPLE: int = 5      # Was 3
    RETRIEVAL_TOP_K_MODERATE: int = 7    # Was 5
    RETRIEVAL_TOP_K_COMPLEX: int = 10
    RETRIEVAL_CANDIDATES: int = 30
    SIMILARITY_THRESHOLD: float = 0.25   # Lower for better recall
    CONTEXT_MAX_TOKENS: int = 3000       # Increased from 2000

    # Cache TTL
    QUERY_CACHE_TTL: int = 3600
    CONVERSATION_TTL: int = 86400
    PROGRESS_TTL: int = 3600
    PASSWORD_PENDING_TTL: int = 900

    # Monitoring
    SENTRY_DSN: str = ""
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()