"""
Database connection pool using asyncpg
"""
import asyncpg
from typing import Optional
from app.config import settings
from loguru import logger

class Database:
    """Async PostgreSQL connection pool manager"""
    
    pool: Optional[asyncpg.Pool] = None
    
    @classmethod
    async def connect(cls):
        """Create connection pool"""
        if cls.pool is None:
            try:
                cls.pool = await asyncpg.create_pool(
                    dsn=settings.DATABASE_URL,
                    min_size=settings.DB_MIN_CONNECTIONS,
                    max_size=settings.DB_MAX_CONNECTIONS,
                    command_timeout=60
                )
                logger.info("PostgreSQL connection pool created")
            except Exception as e:
                logger.error(f"Failed to connect to database: {e}")
                raise
    
    @classmethod
    async def disconnect(cls):
        """Close all connections"""
        if cls.pool:
            await cls.pool.close()
            cls.pool = None
            logger.info("PostgreSQL connection pool closed")
    
    @classmethod
    async def fetch(cls, query: str, *args):
        """Fetch multiple rows"""
        async with cls.pool.acquire() as conn:
            return await conn.fetch(query, *args)
    
    @classmethod
    async def fetchrow(cls, query: str, *args):
        """Fetch single row"""
        async with cls.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)
    
    @classmethod
    async def fetchval(cls, query: str, *args):
        """Fetch single value"""
        async with cls.pool.acquire() as conn:
            return await conn.fetchval(query, *args)
    
    @classmethod
    async def execute(cls, query: str, *args):
        """Execute query (INSERT/UPDATE/DELETE)"""
        async with cls.pool.acquire() as conn:
            return await conn.execute(query, *args)

db = Database()
