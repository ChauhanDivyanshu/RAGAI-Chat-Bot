"""
Retrieval Service - Advanced Vector Search with Reranking
Production-grade retrieval for maximum accuracy
"""
from typing import List, Dict, Optional
from loguru import logger
from app.database.connection import db
from app.services.upload.embedder import embedder


class RetrievalService:
    """Advanced retrieval with hybrid search + reranking"""
    
    def __init__(self):
        self.reranker = None  # Lazy load
        self._reranker_loaded = False
    
    def _load_reranker(self):
        """Lazy load cross-encoder reranker"""
        if self._reranker_loaded:
            return
        
        try:
            from sentence_transformers import CrossEncoder
            logger.info(" Loading reranker model...")
            self.reranker = CrossEncoder(
                'cross-encoder/ms-marco-MiniLM-L-6-v2',
                max_length=512
            )
            self._reranker_loaded = True
            logger.info(" Reranker loaded successfully")
        except Exception as e:
            logger.warning(f" Reranker load failed: {e}. Using vector search only.")
            self._reranker_loaded = False
    
    async def search(
        self,
        query: str,
        top_k: int = 5,
        similarity_threshold: float = 0.25,  # Lower for better recall
        document_id: Optional[str] = None,
        use_reranking: bool = True
    ) -> List[Dict]:
        """
        High-accuracy retrieval pipeline:
        1. Vector search (get more candidates)
        2. Rerank with cross-encoder
        3. Filter by score
        4. Return top K
        """
        if not query or not query.strip():
            return []
        
        logger.info(f" Searching: '{query[:80]}' (top_k={top_k})")
        
        # Step 1: Get more candidates for reranking
        initial_k = top_k * 4 if use_reranking else top_k
        initial_k = min(initial_k, 20)  # Cap at 20
        
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
        
        params.append(initial_k)
        
        try:
            rows = await db.fetch(sql, *params)
            
            # Convert to dict
            candidates = []
            for row in rows:
                score = float(row['similarity_score'])
                candidates.append({
                    'chunk_id': str(row['id']),
                    'document_id': str(row['document_id']),
                    'document_name': row['document_name'],
                    'content': row['content'],
                    'chunk_index': row['chunk_index'],
                    'page_number': row['page_number'],
                    'token_count': row['token_count'],
                    'similarity_score': round(score, 4)
                })
            
            if not candidates:
                logger.warning(" No chunks found")
                return []
            
            logger.info(f" Found {len(candidates)} candidates")
            
            # Step 2: Rerank if enabled
            if use_reranking and len(candidates) > 1:
                self._load_reranker()
                if self._reranker_loaded:
                    candidates = self._rerank(query, candidates)
            
            # Step 3: Filter by threshold (use combined score)
            filtered = []
            for c in candidates:
                # Use rerank score if available, else similarity
                final_score = c.get('rerank_score', c['similarity_score'])
                if final_score >= similarity_threshold:
                    filtered.append(c)
            
            # Step 4: Return top K
            results = filtered[:top_k]
            
            logger.info(
                f" Returning {len(results)} chunks "
                f"(scores: {[round(r.get('rerank_score', r['similarity_score']), 2) for r in results]})"
            )
            
            return results
            
        except Exception as e:
            logger.error(f" Search failed: {e}")
            raise
    
    def _rerank(self, query: str, candidates: List[Dict]) -> List[Dict]:
        """Rerank using cross-encoder for better accuracy"""
        try:
            pairs = [(query, c['content']) for c in candidates]
            scores = self.reranker.predict(pairs)
            
            # Normalize scores to 0-1 range
            min_score = min(scores)
            max_score = max(scores)
            score_range = max_score - min_score if max_score != min_score else 1
            
            for c, score in zip(candidates, scores):
                normalized = (float(score) - min_score) / score_range
                # Combine: 70% rerank + 30% vector similarity
                c['rerank_score'] = round(
                    0.7 * normalized + 0.3 * c['similarity_score'], 
                    4
                )
            
            # Sort by combined score
            candidates.sort(key=lambda x: x['rerank_score'], reverse=True)
            
            logger.debug(f" Reranked {len(candidates)} chunks")
            return candidates
            
        except Exception as e:
            logger.warning(f" Rerank failed: {e}, using vector scores")
            return candidates


# Global instance
retriever = RetrievalService()