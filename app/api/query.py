"""
Smart Query Endpoints with Debug
"""
import time
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.config import settings
from app.models import (
    QueryRequest, QueryResponse, QueryStats, SourceInfo,
    SearchRequest, SearchResponse, ChunkResult,
    EmbedRequest, EmbedResponse,
    SimilarityRequest, SimilarityResponse,
    OllamaTestResponse
)
from app.database import chunks
from app.utils import logger, validate_query

router = APIRouter(tags=["Query & Search"])


@router.post("/embed/test", response_model=EmbedResponse)
async def test_embedding(request: EmbedRequest):
    try:
        from app.services.upload.embedder import embedder
        vector = embedder.embed_text(request.text)
        return EmbedResponse(
            text=request.text,
            embedding_dimension=len(vector),
            first_5_values=vector[:5],
            last_5_values=vector[-5:]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/embed/similarity", response_model=SimilarityResponse)
async def test_similarity(request: SimilarityRequest):
    try:
        from app.services.upload.embedder import embedder
        vec1 = embedder.embed_text(request.text1)
        vec2 = embedder.embed_text(request.text2)
        similarity = embedder.cosine_similarity(vec1, vec2)
        
        interpretation = (
            "Very similar" if similarity > 0.8 else
            "Similar" if similarity > 0.6 else
            "Somewhat related" if similarity > 0.4 else
            "Different"
        )
        
        return SimilarityResponse(
            text1=request.text1,
            text2=request.text2,
            similarity_score=round(similarity, 4),
            interpretation=interpretation
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test-ollama", response_model=OllamaTestResponse)
async def test_ollama():
    try:
        from app.services.query.llm_service import llm_service
        result = await llm_service.test_ollama()
        return OllamaTestResponse(**result)
    except Exception as e:
        return OllamaTestResponse(
            status="error",
            model=settings.OLLAMA_MAIN_MODEL,
            error=str(e)
        )


@router.post("/search", response_model=SearchResponse)
async def search_chunks(request: SearchRequest):
    """Vector search without LLM"""
    start_time = time.time()
    
    try:
        clean_query = validate_query(request.query)
        
        from app.services.upload.embedder import embedder
        query_vector = embedder.embed_text(clean_query)
        
        results = await chunks.vector_search(
            query_embedding=query_vector,
            top_k=request.top_k,
            similarity_threshold=request.similarity_threshold,
            document_id=request.document_id
        )
        
        search_time_ms = int((time.time() - start_time) * 1000)
        
        chunk_results = [
            ChunkResult(
                chunk_id=r['chunk_id'],
                document_id=r['document_id'],
                document_name=r['document_name'],
                content=r['content'],
                chunk_index=r['chunk_index'],
                page_number=r['page_number'],
                token_count=r['token_count'],
                similarity_score=r['similarity_score']
            )
            for r in results
        ]
        
        return SearchResponse(
            query=clean_query,
            total_results=len(chunk_results),
            results=chunk_results,
            search_time_ms=search_time_ms
        )
        
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query", response_model=QueryResponse, summary="Smart RAG Query")
async def query_rag(request: QueryRequest):
    """Smart query endpoint with intent detection."""
    start_time = time.time()
    
    try:
        clean_question = validate_query(request.question)
        logger.info(f"Query: '{clean_question[:80]}'")
        
        from app.services.query.intent_classifier import intent_classifier
        intent = intent_classifier.classify(clean_question)
        
        logger.info(f"Intent classified: {intent['intent']} (use_rag: {intent['use_rag']})")
        
        from app.services.query.llm_service import llm_service
        
        retrieval_time_ms = 0
        retrieved_chunks = []
        
        if intent['use_rag']:
            retrieval_start = time.time()
            from app.services.upload.embedder import embedder
            query_vector = embedder.embed_text(clean_question)
            
            # INCREASED top_k for better context
            retrieved_chunks = await chunks.vector_search(
                query_embedding=query_vector,
                top_k=request.top_k or 5,  # Was 3, now 5
                document_id=request.document_id,
                similarity_threshold=0.3  # Lower threshold
            )
            retrieval_time_ms = int((time.time() - retrieval_start) * 1000)
            logger.info(f"Retrieved {len(retrieved_chunks)} chunks")
            
            # LOG ACTUAL CHUNKS for debugging
            for i, chunk in enumerate(retrieved_chunks[:3], 1):
                logger.info(f"Chunk {i} ({chunk['document_name']} p{chunk.get('page_number')}, score: {chunk['similarity_score']}):")
                logger.info(f"  Content: {chunk['content'][:200]}...")
        
        llm_start = time.time()
        result = await llm_service.generate_smart_response(
            query=clean_question,
            context_chunks=retrieved_chunks if intent['use_rag'] else None,
            intent=intent
        )
        llm_time_ms = int((time.time() - llm_start) * 1000)
        total_time_ms = int((time.time() - start_time) * 1000)
        
        sources = [
            SourceInfo(
                document_name=s['document_name'],
                page_number=s.get('page_number'),
                similarity_score=s['similarity_score'],
                preview=s['preview']
            )
            for s in result['sources']
        ]
        
        logger.info(f"Query done in {total_time_ms}ms (intent: {result.get('intent', 'unknown')})")
        
        return QueryResponse(
            question=clean_question,
            answer=result['answer'],
            sources=sources,
            stats=QueryStats(
                chunks_found=len(retrieved_chunks),
                model=result['model'],
                tokens_used=result['tokens_used'],
                retrieval_time_ms=retrieval_time_ms,
                llm_time_ms=llm_time_ms,
                total_time_ms=total_time_ms,
                cached=False,
                detected_language=result.get('language', 'english')
            ),
            conversation_id=request.conversation_id
        )
        
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query/stream", summary="Streaming Smart Query")
async def query_rag_stream(request: QueryRequest):
    """Streaming version"""
    try:
        clean_question = validate_query(request.question)
        
        async def event_generator():
            try:
                yield f"data: {json.dumps({'type': 'start', 'question': clean_question})}\n\n"
                
                from app.services.query.intent_classifier import intent_classifier
                intent = intent_classifier.classify(clean_question)
                
                retrieved_chunks = []
                if intent['use_rag']:
                    from app.services.upload.embedder import embedder
                    query_vector = embedder.embed_text(clean_question)
                    
                    retrieved_chunks = await chunks.vector_search(
                        query_embedding=query_vector,
                        top_k=request.top_k or 5,
                        document_id=request.document_id,
                        similarity_threshold=0.3
                    )
                    
                    sources_data = [
                        {
                            'document_name': c['document_name'],
                            'page_number': c.get('page_number'),
                            'similarity_score': c['similarity_score']
                        }
                        for c in retrieved_chunks
                    ]
                    yield f"data: {json.dumps({'type': 'sources', 'data': sources_data})}\n\n"
                
                from app.services.query.llm_service import llm_service
                result = await llm_service.generate_smart_response(
                    query=clean_question,
                    context_chunks=retrieved_chunks if intent['use_rag'] else None,
                    intent=intent
                )
                
                for char in result['answer']:
                    yield f"data: {json.dumps({'type': 'token', 'content': char})}\n\n"
                
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
                
            except Exception as e:
                logger.error(f"Stream error: {e}")
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
        
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception(f"Stream failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════
# 🐛 DEBUG ENDPOINTS - See what LLM sees
# ═══════════════════════════════════════════════════════

@router.post("/debug/query", summary="🐛 Debug: See full pipeline")
async def debug_query(request: QueryRequest):
    """
    Debug endpoint - see exactly what LLM receives and returns.
    Shows:
    - Retrieved chunks (full content)
    - Context sent to LLM
    - Raw LLM response
    - Final processed answer
    """
    try:
        clean_question = validate_query(request.question)
        
        # Step 1: Embedding
        from app.services.upload.embedder import embedder
        query_vector = embedder.embed_text(clean_question)
        
        # Step 2: Retrieval
        retrieved_chunks = await chunks.vector_search(
            query_embedding=query_vector,
            top_k=10,  # Get more for debug
            similarity_threshold=0.2
        )
        
        # Step 3: Build context
        from app.services.query.llm_service import llm_service
        context = llm_service._build_clean_context(retrieved_chunks[:5])
        
        # Step 4: Get raw LLM response
        from app.services.query.intent_classifier import intent_classifier
        intent = intent_classifier.classify(clean_question)
        
        result = await llm_service.generate_smart_response(
            query=clean_question,
            context_chunks=retrieved_chunks[:5],
            intent=intent
        )
        
        return {
            "question": clean_question,
            "intent": intent,
            "retrieved_chunks": [
                {
                    "rank": i + 1,
                    "document": chunk['document_name'],
                    "page": chunk.get('page_number'),
                    "score": chunk['similarity_score'],
                    "content": chunk['content'],  # FULL content
                    "content_length": len(chunk['content']),
                }
                for i, chunk in enumerate(retrieved_chunks[:5])
            ],
            "context_sent_to_llm": context,
            "context_length": len(context),
            "llm_response": result['answer'],
            "model_used": result['model'],
            "tokens_used": result['tokens_used'],
            "language_detected": result.get('language'),
        }
        
    except Exception as e:
        logger.exception("Debug failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/debug/document/{document_id}", summary="🐛 Debug: See document chunks")
async def debug_document(document_id: str):
    """See all chunks for a specific document"""
    try:
        from app.database import db
        rows = await db.fetch("""
            SELECT id, content, chunk_index, page_number, token_count
            FROM chunks
            WHERE document_id = $1::uuid
            ORDER BY chunk_index
        """, document_id)
        
        return {
            "document_id": document_id,
            "total_chunks": len(rows),
            "chunks": [
                {
                    "id": str(row['id']),
                    "chunk_index": row['chunk_index'],
                    "page_number": row['page_number'],
                    "token_count": row['token_count'],
                    "content": row['content'],
                    "content_length": len(row['content']),
                }
                for row in rows
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/debug/search-test", summary="🐛 Debug: Test search relevance")
async def debug_search_test(query: str, top_k: int = 10):
    """See raw search results with scores"""
    try:
        from app.services.upload.embedder import embedder
        query_vector = embedder.embed_text(query)
        
        results = await chunks.vector_search(
            query_embedding=query_vector,
            top_k=top_k,
            similarity_threshold=0.1
        )
        
        return {
            "query": query,
            "total_results": len(results),
            "results": [
                {
                    "rank": i + 1,
                    "document": r['document_name'],
                    "page": r.get('page_number'),
                    "score": r['similarity_score'],
                    "content_preview": r['content'][:300],
                    "content_length": len(r['content']),
                }
                for i, r in enumerate(results)
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
