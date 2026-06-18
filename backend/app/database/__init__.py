"""Database package - connection and queries"""

from app.database.connection import db, Database
from app.database.queries import (
    UserQueries,
    DocumentQueries,
    ChunkQueries,
    ConversationQueries,
    CacheQueries,
    SystemQueries,
    # Convenience exports
    users,
    documents,
    chunks,
    conversations,
    cache,
    system,
)

__all__ = [
    "db",
    "Database",
    "UserQueries",
    "DocumentQueries",
    "ChunkQueries",
    "ConversationQueries",
    "CacheQueries",
    "SystemQueries",
    "users",
    "documents",
    "chunks",
    "conversations",
    "cache",
    "system",
]
