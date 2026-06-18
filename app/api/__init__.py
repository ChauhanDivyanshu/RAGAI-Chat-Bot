"""
API Routers Package
"""
from app.api.health import router as health_router
from app.api.upload import router as upload_router
from app.api.query import router as query_router
from app.api.documents import router as documents_router
from app.api.webhook import router as webhook_router

__all__ = [
    "health_router",
    "upload_router",
    "query_router",
    "documents_router",
    "webhook_router",
]
