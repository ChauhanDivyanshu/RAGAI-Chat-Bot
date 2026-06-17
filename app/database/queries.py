"""
Centralized Database Queries
All SQL operations in one place for maintainability
"""
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from app.database.connection import db
from app.utils import logger, DatabaseError, vector_to_pg_string


# ═══════════════════════════════════════════════════════
# USER QUERIES
# ═══════════════════════════════════════════════════════

class UserQueries:
    """User-related database operations"""
    
    @staticmethod
    async def create_user(whatsapp_id: str, name: Optional[str] = None, role: str = "user") -> str:
        """Create new user, return user ID"""
        try:
            user_id = await db.fetchval("""
                INSERT INTO users (whatsapp_id, name, role)
                VALUES ($1, $2, $3)
                ON CONFLICT (whatsapp_id) DO UPDATE
                SET last_active_at = NOW()
                RETURNING id
            """, whatsapp_id, name, role)
            return str(user_id)
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            raise DatabaseError(f"User creation failed: {e}")
    
    @staticmethod
    async def get_user_by_whatsapp(whatsapp_id: str) -> Optional[Dict]:
        """Get user by WhatsApp ID"""
        try:
            row = await db.fetchrow(
                "SELECT * FROM users WHERE whatsapp_id = $1",
                whatsapp_id
            )
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"Failed to get user: {e}")
            raise DatabaseError(f"User fetch failed: {e}")
    
    @staticmethod
    async def get_user_by_id(user_id: str) -> Optional[Dict]:
        """Get user by UUID"""
        try:
            row = await db.fetchrow(
                "SELECT * FROM users WHERE id = $1",
                UUID(user_id)
            )
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"Failed to get user: {e}")
            raise DatabaseError(f"User fetch failed: {e}")
    
    @staticmethod
    async def update_user_activity(user_id: str) -> None:
        """Update user's last active timestamp"""
        try:
            await db.execute(
                "UPDATE users SET last_active_at = NOW() WHERE id = $1",
                UUID(user_id)
            )
        except Exception as e:
            logger.error(f"Failed to update user activity: {e}")


# ═══════════════════════════════════════════════════════
# DOCUMENT QUERIES
# ═══════════════════════════════════════════════════════

class DocumentQueries:
    """Document-related database operations"""
    
    @staticmethod
    async def create_document(
        original_name: str,
        file_type: str,
        mime_type: str,
        file_size: int,
        file_hash: str,
        user_id: Optional[str] = None,
        page_count: Optional[int] = None,
        word_count: Optional[int] = None,
        language: Optional[str] = None,
        status: str = "processing"
    ) -> str:
        """Create new document record, return document ID"""
        try:
            doc_id = await db.fetchval("""
                INSERT INTO documents (
                    user_id, original_name, file_type, mime_type, 
                    file_size, file_hash, page_count, word_count, 
                    language, status
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                RETURNING id
            """,
                UUID(user_id) if user_id else None,
                original_name, file_type, mime_type,
                file_size, file_hash, page_count, word_count,
                language, status
            )
            logger.info(f"Document created: {doc_id}")
            return str(doc_id)
        except Exception as e:
            logger.error(f"Failed to create document: {e}")
            raise DatabaseError(f"Document creation failed: {e}")
    
    @staticmethod
    async def get_by_hash(file_hash: str) -> Optional[Dict]:
        """Check if document with this hash exists (deduplication)"""
        try:
            row = await db.fetchrow(
                "SELECT id, original_name, status, created_at FROM documents WHERE file_hash = $1",
                file_hash
            )
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"Failed to check duplicate: {e}")
            raise DatabaseError(f"Hash check failed: {e}")
    
    @staticmethod
    async def get_by_id(document_id: str) -> Optional[Dict]:
        """Get document by ID"""
        try:
            row = await db.fetchrow(
                "SELECT * FROM documents WHERE id = $1",
                UUID(document_id)
            )
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"Failed to get document: {e}")
            raise DatabaseError(f"Document fetch failed: {e}")
    
    @staticmethod
    async def update_status(
        document_id: str,
        status: str,
        error_message: Optional[str] = None,
        processing_time: Optional[float] = None
    ) -> None:
        """Update document processing status"""
        try:
            if status == "completed":
                await db.execute("""
                    UPDATE documents 
                    SET status = $1, processed_at = NOW(), processing_time = $2
                    WHERE id = $3
                """, status, processing_time, UUID(document_id))
            elif status == "failed":
                await db.execute("""
                    UPDATE documents 
                    SET status = $1, error_message = $2, processed_at = NOW()
                    WHERE id = $3
                """, status, error_message, UUID(document_id))
            else:
                await db.execute(
                    "UPDATE documents SET status = $1 WHERE id = $2",
                    status, UUID(document_id)
                )
        except Exception as e:
            logger.error(f"Failed to update document status: {e}")
            raise DatabaseError(f"Status update failed: {e}")
    
    @staticmethod
    async def list_documents(
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None,
        file_type: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> List[Dict]:
        """List documents with filters"""
        try:
            conditions = []
            params = []
            param_idx = 1
            
            if status:
                conditions.append(f"d.status = ${param_idx}")
                params.append(status)
                param_idx += 1
            
            if file_type:
                conditions.append(f"d.file_type = ${param_idx}")
                params.append(file_type)
                param_idx += 1
            
            if user_id:
                conditions.append(f"d.user_id = ${param_idx}")
                params.append(UUID(user_id))
                param_idx += 1
            
            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
            
            query = f"""
                SELECT 
                    d.id, d.original_name, d.file_type, d.file_size,
                    d.page_count, d.status, d.language,
                    d.created_at, d.processed_at,
                    COUNT(c.id) as chunk_count
                FROM documents d
                LEFT JOIN chunks c ON c.document_id = d.id
                {where_clause}
                GROUP BY d.id
                ORDER BY d.created_at DESC
                LIMIT ${param_idx} OFFSET ${param_idx + 1}
            """
            params.extend([limit, offset])
            
            rows = await db.fetch(query, *params)
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to list documents: {e}")
            raise DatabaseError(f"Document listing failed: {e}")
    
    @staticmethod
    async def count_documents(status: Optional[str] = None) -> int:
        """Count total documents"""
        try:
            if status:
                count = await db.fetchval(
                    "SELECT COUNT(*) FROM documents WHERE status = $1",
                    status
                )
            else:
                count = await db.fetchval("SELECT COUNT(*) FROM documents")
            return count or 0
        except Exception as e:
            logger.error(f"Failed to count documents: {e}")
            return 0
    
    @staticmethod
    async def delete_document(document_id: str) -> bool:
        """Delete document and all its chunks (CASCADE)"""
        try:
            result = await db.execute(
                "DELETE FROM documents WHERE id = $1",
                UUID(document_id)
            )
            deleted = "DELETE 1" in result
            if deleted:
                logger.info(f"Document deleted: {document_id}")
            return deleted
        except Exception as e:
            logger.error(f"Failed to delete document: {e}")
            raise DatabaseError(f"Document deletion failed: {e}")


# ═══════════════════════════════════════════════════════
# CHUNK QUERIES
# ═══════════════════════════════════════════════════════

class ChunkQueries:
    """Chunk-related database operations"""
    
    @staticmethod
    async def insert_chunk(
        document_id: str,
        content: str,
        content_hash: str,
        embedding: List[float],
        chunk_index: int,
        page_number: Optional[int] = None,
        token_count: Optional[int] = None,
        chunk_type: str = "text",
        metadata: Optional[Dict] = None
    ) -> Optional[str]:
        """Insert single chunk with embedding"""
        try:
            import json
            vector_str = vector_to_pg_string(embedding)
            
            chunk_id = await db.fetchval("""
                INSERT INTO chunks (
                    document_id, content, content_hash, embedding,
                    chunk_index, page_number, token_count, chunk_type, metadata
                ) VALUES ($1, $2, $3, $4::vector, $5, $6, $7, $8, $9)
                ON CONFLICT (document_id, content_hash) DO NOTHING
                RETURNING id
            """,
                UUID(document_id), content, content_hash, vector_str,
                chunk_index, page_number, token_count, chunk_type,
                json.dumps(metadata or {})
            )
            return str(chunk_id) if chunk_id else None
        except Exception as e:
            logger.error(f"Failed to insert chunk {chunk_index}: {e}")
            return None
    
    @staticmethod
    async def insert_chunks_batch(
        document_id: str,
        chunks: List[Dict],
        embeddings: List[List[float]]
    ) -> int:
        """Insert multiple chunks efficiently"""
        import json
        from app.utils import generate_content_hash
        
        saved_count = 0
        
        try:
            async with db.pool.acquire() as conn:
                async with conn.transaction():
                    for chunk, embedding in zip(chunks, embeddings):
                        try:
                            content_hash = generate_content_hash(chunk['content'])
                            vector_str = vector_to_pg_string(embedding)
                            
                            result = await conn.fetchval("""
                                INSERT INTO chunks (
                                    document_id, content, content_hash, embedding,
                                    chunk_index, page_number, token_count, chunk_type, metadata
                                ) VALUES ($1, $2, $3, $4::vector, $5, $6, $7, $8, $9)
                                ON CONFLICT (document_id, content_hash) DO NOTHING
                                RETURNING id
                            """,
                                UUID(document_id),
                                chunk['content'],
                                content_hash,
                                vector_str,
                                chunk['chunk_index'],
                                chunk.get('page_number'),
                                chunk.get('token_count'),
                                chunk.get('chunk_type', 'text'),
                                json.dumps(chunk.get('metadata', {}))
                            )
                            if result:
                                saved_count += 1
                        except Exception as e:
                            logger.warning(f"Skipped chunk {chunk['chunk_index']}: {e}")
            
            logger.info(f"Saved {saved_count}/{len(chunks)} chunks for document {document_id}")
            return saved_count
        except Exception as e:
            logger.error(f"Batch chunk insert failed: {e}")
            raise DatabaseError(f"Chunk batch insert failed: {e}")
    
    @staticmethod
    async def vector_search(
        query_embedding: List[float],
        top_k: int = 5,
        similarity_threshold: float = 0.3,
        document_id: Optional[str] = None
    ) -> List[Dict]:
        """Cosine similarity search using pgvector"""
        try:
            vector_str = vector_to_pg_string(query_embedding)
            
            if document_id:
                rows = await db.fetch("""
                    SELECT 
                        c.id, c.document_id, c.content, c.chunk_index,
                        c.page_number, c.token_count, c.chunk_type,
                        d.original_name as document_name,
                        1 - (c.embedding <=> $1::vector) as similarity_score
                    FROM chunks c
                    JOIN documents d ON d.id = c.document_id
                    WHERE c.embedding IS NOT NULL AND c.document_id = $2
                    ORDER BY c.embedding <=> $1::vector
                    LIMIT $3
                """, vector_str, UUID(document_id), top_k)
            else:
                rows = await db.fetch("""
                    SELECT 
                        c.id, c.document_id, c.content, c.chunk_index,
                        c.page_number, c.token_count, c.chunk_type,
                        d.original_name as document_name,
                        1 - (c.embedding <=> $1::vector) as similarity_score
                    FROM chunks c
                    JOIN documents d ON d.id = c.document_id
                    WHERE c.embedding IS NOT NULL
                    ORDER BY c.embedding <=> $1::vector
                    LIMIT $2
                """, vector_str, top_k)
            
            results = []
            for row in rows:
                score = float(row['similarity_score'])
                if score >= similarity_threshold:
                    results.append({
                        'chunk_id': str(row['id']),
                        'document_id': str(row['document_id']),
                        'document_name': row['document_name'],
                        'content': row['content'],
                        'chunk_index': row['chunk_index'],
                        'page_number': row['page_number'],
                        'token_count': row['token_count'],
                        'chunk_type': row['chunk_type'],
                        'similarity_score': round(score, 4)
                    })
            
            return results
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            raise DatabaseError(f"Search failed: {e}")
    
    @staticmethod
    async def count_chunks(document_id: Optional[str] = None) -> int:
        """Count chunks"""
        try:
            if document_id:
                count = await db.fetchval(
                    "SELECT COUNT(*) FROM chunks WHERE document_id = $1",
                    UUID(document_id)
                )
            else:
                count = await db.fetchval("SELECT COUNT(*) FROM chunks")
            return count or 0
        except Exception as e:
            logger.error(f"Failed to count chunks: {e}")
            return 0


# ═══════════════════════════════════════════════════════
# CONVERSATION QUERIES
# ═══════════════════════════════════════════════════════

class ConversationQueries:
    """Conversation and message operations"""
    
    @staticmethod
    async def create_conversation(user_id: str, session_id: Optional[str] = None) -> str:
        """Create new conversation"""
        try:
            conv_id = await db.fetchval("""
                INSERT INTO conversations (user_id, session_id)
                VALUES ($1, $2)
                RETURNING id
            """, UUID(user_id), session_id)
            return str(conv_id)
        except Exception as e:
            logger.error(f"Failed to create conversation: {e}")
            raise DatabaseError(f"Conversation creation failed: {e}")
    
    @staticmethod
    async def add_message(
        conversation_id: str,
        role: str,
        content: str,
        chunks_used: Optional[List[str]] = None,
        model_used: Optional[str] = None,
        tokens_input: Optional[int] = None,
        tokens_output: Optional[int] = None,
        latency_ms: Optional[int] = None
    ) -> str:
        """Add message to conversation"""
        try:
            chunk_uuids = [UUID(c) for c in chunks_used] if chunks_used else None
            
            msg_id = await db.fetchval("""
                INSERT INTO messages (
                    conversation_id, role, content, chunks_used,
                    model_used, tokens_input, tokens_output, latency_ms
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING id
            """,
                UUID(conversation_id), role, content, chunk_uuids,
                model_used, tokens_input, tokens_output, latency_ms
            )
            
            # Update conversation message count
            await db.execute("""
                UPDATE conversations 
                SET message_count = message_count + 1 
                WHERE id = $1
            """, UUID(conversation_id))
            
            return str(msg_id)
        except Exception as e:
            logger.error(f"Failed to add message: {e}")
            raise DatabaseError(f"Message add failed: {e}")
    
    @staticmethod
    async def get_recent_messages(conversation_id: str, limit: int = 10) -> List[Dict]:
        """Get recent messages from conversation"""
        try:
            rows = await db.fetch("""
                SELECT id, role, content, created_at
                FROM messages
                WHERE conversation_id = $1
                ORDER BY created_at DESC
                LIMIT $2
            """, UUID(conversation_id), limit)
            
            messages = [dict(row) for row in rows]
            return list(reversed(messages))  # Chronological order
        except Exception as e:
            logger.error(f"Failed to get messages: {e}")
            raise DatabaseError(f"Messages fetch failed: {e}")


# ═══════════════════════════════════════════════════════
# CACHE QUERIES
# ═══════════════════════════════════════════════════════

class CacheQueries:
    """Query cache operations"""
    
    @staticmethod
    async def get_cached_response(query_hash: str) -> Optional[Dict]:
        """Get cached response if not expired"""
        try:
            row = await db.fetchrow("""
                SELECT cached_response, hit_count
                FROM query_cache
                WHERE query_hash = $1 
                  AND (expires_at IS NULL OR expires_at > NOW())
            """, query_hash)
            
            if row:
                # Update hit count
                await db.execute("""
                    UPDATE query_cache 
                    SET hit_count = hit_count + 1, last_hit_at = NOW()
                    WHERE query_hash = $1
                """, query_hash)
                
                return dict(row['cached_response']) if row['cached_response'] else None
            return None
        except Exception as e:
            logger.error(f"Cache fetch failed: {e}")
            return None
    
    @staticmethod
    async def save_response(
        query_hash: str,
        original_query: str,
        response: Dict,
        ttl_seconds: int = 3600
    ) -> None:
        """Cache query response"""
        try:
            import json
            await db.execute("""
                INSERT INTO query_cache (
                    query_hash, original_query, cached_response, expires_at
                ) VALUES ($1, $2, $3, NOW() + INTERVAL '1 second' * $4)
                ON CONFLICT (query_hash) DO UPDATE
                SET cached_response = $3, 
                    expires_at = NOW() + INTERVAL '1 second' * $4,
                    last_hit_at = NOW()
            """, query_hash, original_query, json.dumps(response), ttl_seconds)
        except Exception as e:
            logger.error(f"Cache save failed: {e}")


# ═══════════════════════════════════════════════════════
# SYSTEM QUERIES
# ═══════════════════════════════════════════════════════

class SystemQueries:
    """System info and health queries"""
    
    @staticmethod
    async def health_check() -> bool:
        """Quick database health check"""
        try:
            result = await db.fetchval("SELECT 1")
            return result == 1
        except Exception:
            return False
    
    @staticmethod
    async def get_db_info() -> Dict[str, Any]:
        """Get database tables, extensions, counts"""
        try:
            tables = await db.fetch(
                "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename"
            )
            extensions = await db.fetch(
                "SELECT extname FROM pg_extension ORDER BY extname"
            )
            doc_count = await db.fetchval("SELECT COUNT(*) FROM documents")
            chunk_count = await db.fetchval("SELECT COUNT(*) FROM chunks")
            user_count = await db.fetchval("SELECT COUNT(*) FROM users")
            
            return {
                "tables": [t['tablename'] for t in tables],
                "extensions": [e['extname'] for e in extensions],
                "documents_count": doc_count or 0,
                "chunks_count": chunk_count or 0,
                "users_count": user_count or 0
            }
        except Exception as e:
            logger.error(f"DB info fetch failed: {e}")
            raise DatabaseError(f"DB info failed: {e}")


# Convenience exports
users = UserQueries
documents = DocumentQueries
chunks = ChunkQueries
conversations = ConversationQueries
cache = CacheQueries
system = SystemQueries
