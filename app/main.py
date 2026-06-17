"""
RAG System - Main FastAPI Application
Production-grade WhatsApp RAG Chatbot Backend
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.config import settings
from app.database import db
from app.middleware import setup_middleware
from app.api import (
    health_router,
    upload_router,
    query_router,
    documents_router,
)
from app.utils import logger


# ═══════════════════════════════════════════════════════
# LIFESPAN MANAGER (Startup & Shutdown)
# ═══════════════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # ─── STARTUP ───
    logger.info("=" * 60)
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug Mode: {settings.DEBUG}")
    logger.info("=" * 60)
    
    # Connect to database
    try:
        await db.connect()
        logger.info("Database connection pool ready")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise
    
    # Pre-load embedding model (optional - speeds up first request)
    try:
        from app.services.upload.embedder import embedder
        logger.info("Pre-loading embedding model...")
        embedder.load_model()
        logger.info("Embedding model ready")
    except Exception as e:
        logger.warning(f"Could not pre-load embedding model: {e}")
    
    logger.info("=" * 60)
    logger.info("RAG System started successfully")
    logger.info(f"API Docs: http://localhost:8000/docs")
    logger.info("=" * 60)
    
    yield  # Application runs here
    
    # ─── SHUTDOWN ───
    logger.info("Shutting down RAG System...")
    await db.disconnect()
    logger.info("Cleanup complete. Goodbye!")


# ═══════════════════════════════════════════════════════
# FASTAPI APP INITIALIZATION
# ═══════════════════════════════════════════════════════

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    ## RAG System API
    
    Production-grade Retrieval Augmented Generation system with:
    
    - **Multi-format document support** (PDF, DOCX, Excel, etc.)
    - **Multilingual embeddings** (BGE-M3)
    - **Vector search** (PostgreSQL + pgvector)
    - **LLM generation** (Ollama Llama 3.1)
    - **WhatsApp integration** ready
    
    ### Quick Start
    1. Upload documents via `POST /upload/pdf`
    2. Search chunks via `POST /search`
    3. Ask questions via `POST /query` (Main RAG endpoint)
    """,
    debug=settings.DEBUG,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    contact={
        "name": "RAG System Support",
        "email": "support@example.com",
    },
    license_info={
        "name": "MIT License",
    },
)


# ═══════════════════════════════════════════════════════
# MIDDLEWARE SETUP
# ═══════════════════════════════════════════════════════

setup_middleware(app)


# ═══════════════════════════════════════════════════════
# REGISTER ROUTERS
# ═══════════════════════════════════════════════════════

app.include_router(health_router)
app.include_router(upload_router)
app.include_router(query_router)
app.include_router(documents_router)


# ═══════════════════════════════════════════════════════
# CUSTOM OPENAPI TAGS METADATA
# ═══════════════════════════════════════════════════════

app.openapi_tags = [
    {
        "name": "Health & System",
        "description": "System health checks and database information",
    },
    {
        "name": "Upload",
        "description": "Document upload and processing endpoints",
    },
    {
        "name": "Query & Search",
        "description": "RAG query, vector search, and embeddings",
    },
    {
        "name": "Documents",
        "description": "Document management (list, get, delete)",
    },
]
