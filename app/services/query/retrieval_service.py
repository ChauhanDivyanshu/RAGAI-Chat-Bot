"""
Retrieval Service - Vector Search with pgvector
"""
from typing import List, Dict, Optional
from loguru import logger
from app.database.connection import db
from app.services.upload.embedder import embedder


class RetrievalService:
    """Search for relevant chunks using vector similarity"""
    
    async def search(
        self,
        query: str,
        top_k: int = 5,
        similarity_threshold: float = 0.3,
        document_id: Optional[str] = None
    ) -> List[Dict]:
        """
        Search for most relevant chunks
        
        Args:
            query: User question
            top_k: Number of chunks to retrieve
            similarity_threshold: Min similarity score (0-1)
            document_id: Optional - search only in specific document
            
        Returns:
            List of relevant chunks with scores
        """
        if not query or not query.strip():
            return []
        
        logger.info(f"Searching for: '{query}' (top_k={top_k})")
        
        # Generate query embedding
        query_vector = embedder.embed_text(query)
        vector_str = "[" + ",".join(map(str, query_vector)) + "]"
        
        # Build query
        sql = """
            SELECT 
                c.id,
                c.document_id,
                c.content,
                c.chunk_index,
                c.page_number,
                c.token_count,
                d.original_name as document_name,
                1 - (c.embedding <=> $1::vector) as similarity_score
            FROM chunks c
            JOIN documents d ON d.id = c.document_id
            WHERE c.embedding IS NOT NULL
        """
        
        params = [vector_str]
        
        if document_id:
            sql += " AND c.document_id = $2"
            params.append(document_id)
            sql += f" ORDER BY c.embedding <=> $1::vector LIMIT ${len(params) + 1}"
        else:
            sql += " ORDER BY c.embedding <=> $1::vector LIMIT $2"
        
        params.append(top_k)
        
        try:
            rows = await db.fetch(sql, *params)
            
            # Filter by threshold
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
                        'similarity_score': round(score, 4)
                    })
            
            logger.info(f"Found {len(results)} relevant chunks")
            return results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise


# Global instance
retriever = RetrievalService()
