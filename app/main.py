"""
RAG System - Main FastAPI Application with WhatsApp Integration
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
    webhook_router,
)
from app.utils import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 60)
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info("=" * 60)
    
    try:
        await db.connect()
        logger.info("Database connection pool ready")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise
    
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
    logger.info(f"WhatsApp Webhook: http://localhost:8000/webhook/whatsapp")
    logger.info("=" * 60)
    
    yield
    
    logger.info("Shutting down RAG System...")
    await db.disconnect()
    logger.info("Goodbye!")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="RAG System with WhatsApp Integration",
    debug=settings.DEBUG,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Middleware
setup_middleware(app)

# Routers
app.include_router(health_router)
app.include_router(upload_router)
app.include_router(query_router)
app.include_router(documents_router)
app.include_router(webhook_router)

app.openapi_tags = [
    {"name": "Health & System", "description": "System health"},
    {"name": "Upload", "description": "Document upload"},
    {"name": "Query & Search", "description": "RAG queries"},
    {"name": "Documents", "description": "Document management"},
    {"name": "WhatsApp Webhook", "description": "WhatsApp integration"},
]
