"""
Query & Search Endpoints (RAG) - OPTIMIZED
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


# ─────────────────────────────────────
# EMBEDDING TEST ENDPOINTS
# ─────────────────────────────────────

@router.post("/embed/test", response_model=EmbedResponse)
async def test_embedding(request: EmbedRequest):
    """Generate embedding for text (1024-dim vector)"""
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
        logger.error(f"Embedding test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/embed/similarity", response_model=SimilarityResponse)
async def test_similarity(request: SimilarityRequest):
    """Compare semantic similarity between two texts"""
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


# ─────────────────────────────────────
# OLLAMA TEST
# ─────────────────────────────────────

@router.get("/test-ollama", response_model=OllamaTestResponse)
async def test_ollama():
    """Test Ollama connectivity"""
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


# ─────────────────────────────────────
# SEARCH ENDPOINT
# ─────────────────────────────────────

@router.post("/search", response_model=SearchResponse)
async def search_chunks(request: SearchRequest):
    """Vector search without LLM (fast)"""
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


# ─────────────────────────────────────
# MAIN RAG QUERY (OPTIMIZED)
# ─────────────────────────────────────

@router.post("/query", response_model=QueryResponse, summary="RAG Query (full response)")
async def query_rag(request: QueryRequest):
    """
    Main RAG endpoint - returns complete answer.
    
    For better UX on slow systems, use /query/stream instead.
    """
    start_time = time.time()
    
    try:
        clean_question = validate_query(request.question)
        logger.info(f"Query: '{clean_question[:80]}'")
        
        # OPTIMIZATION: Reduce top_k for faster LLM
        actual_top_k = min(request.top_k or 5, 3)  # Max 3 chunks
        
        # Retrieval
        retrieval_start = time.time()
        from app.services.upload.embedder import embedder
        query_vector = embedder.embed_text(clean_question)
        
        retrieved_chunks = await chunks.vector_search(
            query_embedding=query_vector,
            top_k=actual_top_k,
            document_id=request.document_id
        )
        retrieval_time_ms = int((time.time() - retrieval_start) * 1000)
        
        if not retrieved_chunks:
            total_time_ms = int((time.time() - start_time) * 1000)
            return QueryResponse(
                question=clean_question,
                answer="No relevant information found in uploaded documents.",
                sources=[],
                stats=QueryStats(
                    chunks_found=0,
                    model=settings.OLLAMA_MAIN_MODEL,
                    tokens_used=0,
                    retrieval_time_ms=retrieval_time_ms,
                    llm_time_ms=0,
                    total_time_ms=total_time_ms,
                    cached=False
                )
            )
        
        # LLM Generation
        llm_start = time.time()
        from app.services.query.llm_service import llm_service
        result = await llm_service.generate_answer(
            query=clean_question,
            context_chunks=retrieved_chunks,
            temperature=request.temperature or 0.1
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
        
        logger.info(f"Query done in {total_time_ms}ms (retrieval: {retrieval_time_ms}ms, LLM: {llm_time_ms}ms)")
        
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
                cached=False
            ),
            conversation_id=request.conversation_id
        )
        
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────
# STREAMING RAG QUERY (BETTER UX)
# ─────────────────────────────────────

@router.post("/query/stream", summary="RAG Query (streaming response)")
async def query_rag_stream(request: QueryRequest):
    """
    STREAMING RAG endpoint - tokens stream as generated.
    
    Better UX for slow LLMs - user sees answer building up.
    Returns Server-Sent Events (SSE).
    """
    try:
        clean_question = validate_query(request.question)
        logger.info(f"Streaming query: '{clean_question[:80]}'")
        
        async def event_generator():
            try:
                # Send start event
                yield f"data: {json.dumps({'type': 'start', 'question': clean_question})}\n\n"
                
                # Retrieval
                from app.services.upload.embedder import embedder
                query_vector = embedder.embed_text(clean_question)
                
                actual_top_k = min(request.top_k or 5, 3)
                retrieved_chunks = await chunks.vector_search(
                    query_embedding=query_vector,
                    top_k=actual_top_k,
                    document_id=request.document_id
                )
                
                # Send sources event
                sources_data = [
                    {
                        'document_name': c['document_name'],
                        'page_number': c.get('page_number'),
                        'similarity_score': c['similarity_score']
                    }
                    for c in retrieved_chunks
                ]
                yield f"data: {json.dumps({'type': 'sources', 'data': sources_data})}\n\n"
                
                if not retrieved_chunks:
                    yield f"data: {json.dumps({'type': 'answer', 'content': 'No relevant information found.'})}\n\n"
                    yield f"data: {json.dumps({'type': 'done'})}\n\n"
                    return
                
                # Stream LLM response
                from app.services.query.llm_service import llm_service
                async for token in llm_service.generate_answer_streaming(
                    query=clean_question,
                    context_chunks=retrieved_chunks,
                    temperature=request.temperature or 0.1
                ):
                    yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
                
                # Send done event
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
        logger.exception(f"Stream query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
