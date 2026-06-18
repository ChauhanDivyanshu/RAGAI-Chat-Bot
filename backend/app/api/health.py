"""
Health & System Information Endpoints
"""
from fastapi import APIRouter
from datetime import datetime

from app.config import settings
from app.database import system
from app.models import HealthResponse, DBInfoResponse
from app.utils import logger

router = APIRouter(prefix="", tags=["Health & System"])


@router.get("/", summary="Root endpoint")
async def root():
    """API root - basic info"""
    return {
        "message": "RAG System API",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "docs": "/docs",
        "endpoints": {
            "health": "GET /health",
            "db_info": "GET /db-info",
            "upload": "POST /upload/pdf",
            "search": "POST /search",
            "query": "POST /query (Main RAG endpoint)",
            "documents": "GET /documents"
        }
    }


@router.get("/health", response_model=HealthResponse, summary="System health check")
async def health_check():
    """
    Comprehensive health check:
    - API status
    - Database connectivity
    - Service versions
    """
    db_healthy = await system.health_check()
    db_status = "healthy" if db_healthy else "unhealthy"
    
    return HealthResponse(
        status="healthy" if db_healthy else "degraded",
        version=settings.APP_VERSION,
        database=db_status,
        timestamp=datetime.utcnow().isoformat()
    )


@router.get("/db-info", response_model=DBInfoResponse, summary="Database information")
async def db_info():
    """
    Get database information:
    - All tables
    - Installed extensions
    - Document and chunk counts
    """
    info = await system.get_db_info()
    return DBInfoResponse(**info)
