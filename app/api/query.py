"""
Smart Query Endpoints - Production Ready with Groq
"""
import time
import json
from typing import Dict, List, Optional
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


# ═══════════════════════════════════════════════════════
# 🎯 MAIN RAG QUERY ENDPOINT
# ═══════════════════════════════════════════════════════

@router.post("/query", response_model=QueryResponse, summary="Smart RAG Query")
async def query_rag(request: QueryRequest):
    """
    PRODUCTION-GRADE RAG with Smart Routing
    
    Logic:
    1. Quick check: Is this about real-time/general knowledge? → Web first
    2. Try documents
    3. If docs found → Use them
    4. If no docs OR poor answer → Web search
    """
    start_time = time.time()
    
    try:
        clean_question = validate_query(request.question)
        logger.info(f"📩 Query: '{clean_question[:80]}'")
        
        # Step 1: Classify intent
        from app.services.query.intent_classifier import intent_classifier
        intent = intent_classifier.classify(clean_question)
        logger.info(f"🎯 Intent: {intent['intent']} | RAG: {intent['use_rag']}")
        
        from app.services.query.llm_service import llm_service
        
        retrieval_time_ms = 0
        retrieved_chunks = []
        used_web_search = False
        
        # ⚡ SHORTCUT: Real-time queries go straight to web
        if _is_realtime_query(clean_question):
            logger.info("⚡ Real-time query detected → Web search first")
            return await _handle_web_query(
                clean_question, intent, llm_service, start_time, request
            )
        
        # Step 2: Document RAG
        if intent['use_rag']:
            retrieval_start = time.time()
            
            from app.services.query.retrieval_service import retriever
            
            retrieved_chunks = await retriever.search(
                query=clean_question,
                top_k=request.top_k or 3,
                similarity_threshold=0.4,  # Higher threshold - only good matches
                document_id=request.document_id,
                use_reranking=True
            )
            
            retrieval_time_ms = int((time.time() - retrieval_start) * 1000)
            logger.info(f"📚 Retrieved {len(retrieved_chunks)} chunks in {retrieval_time_ms}ms")
            
            # Check chunk quality - if all scores low, try web
            if retrieved_chunks:
                max_score = max(c.get('rerank_score', c['similarity_score']) for c in retrieved_chunks)
                if max_score < 0.5:
                    logger.info(f"⚠️ Low chunk quality ({max_score:.2f}) → Try web")
                    return await _handle_web_query(
                        clean_question, intent, llm_service, start_time, request, retrieved_chunks
                    )
        
        # Step 3: Generate response
        llm_start = time.time()
        
        # No chunks at all + RAG intent → Web fallback
        if intent['use_rag'] and len(retrieved_chunks) == 0:
            logger.info("🌐 No documents → Web search fallback")
            return await _handle_web_query(
                clean_question, intent, llm_service, start_time, request
            )
        
        # Normal flow
        result = await llm_service.generate_smart_response(
            query=clean_question,
            context_chunks=retrieved_chunks if intent['use_rag'] else None,
            intent=intent
        )
        
        # Quality check
        if (intent['use_rag'] 
            and len(retrieved_chunks) > 0 
            and _is_unhelpful_answer(result.get('answer', ''))):
            
            logger.info("⚠️ Doc answer unhelpful → Web fallback")
            return await _handle_web_query(
                clean_question, intent, llm_service, start_time, request, retrieved_chunks
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
        
        logger.info(f"✅ Done in {total_time_ms}ms (web: {used_web_search})")
        
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
        logger.exception(f"❌ Query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _handle_web_query(
    query: str, 
    intent: Dict, 
    llm_service, 
    start_time: float,
    request: QueryRequest,
    fallback_chunks: List = None
) -> QueryResponse:
    """Handle web search query"""
    from app.services.query.web_search import web_search
    
    web_start = time.time()
    web_results = await web_search.search(query, max_results=5)
    web_time = int((time.time() - web_start) * 1000)
    
    logger.info(f"🌐 Web search: {len(web_results)} results in {web_time}ms")
    
    language = llm_service.detect_language(query)
    
    if web_results and len(web_results) > 0:
        # Generate response from web
        result = await llm_service.generate_web_search_response(
            query=query,
            web_results=web_results,
            language=language
        )
    else:
        # No web results - use fallback
        result = {
            'answer': _get_no_results_message(language, query),
            'sources': [],
            'model': 'fallback',
            'tokens_used': 0,
            'language': language,
            'intent': 'no_results'
        }
    
    total_time_ms = int((time.time() - start_time) * 1000)
    
    sources = [
        SourceInfo(
            document_name=s.get('document_name', '🌐 Web'),
            page_number=s.get('page_number'),
            similarity_score=s.get('similarity_score', 0.8),
            preview=s.get('preview', '')
        )
        for s in result['sources']
    ]
    
    return QueryResponse(
        question=query,
        answer=result['answer'],
        sources=sources,
        stats=QueryStats(
            chunks_found=0,
            model=result['model'],
            tokens_used=result['tokens_used'],
            retrieval_time_ms=web_time,
            llm_time_ms=total_time_ms - web_time,
            total_time_ms=total_time_ms,
            cached=False,
            detected_language=language
        ),
        conversation_id=request.conversation_id
    )


def _is_realtime_query(query: str) -> bool:
    """Check if query needs real-time/web data"""
    query_lower = query.lower()
    
    realtime_keywords = [
        # Sports
        'match', 'cricket', 'football', 'score', 'ipl', 'live',
        'aaj ka match', 'today match', 'live score',
        
        # Time-sensitive
        'today', 'aaj', 'aaj ki', 'current', 'latest', 'news',
        'weather', 'mausam', 'tapman', 'temperature',
        
        # Stock/Finance
        'stock', 'share price', 'bitcoin', 'crypto', 'rate today',
        
        # General current info
        'who is the', 'kya hai aaj', 'price of', 'cost of',
        
        # Search indicators
        'search', 'find online', 'web pe', 'google',
    ]
    
    for keyword in realtime_keywords:
        if keyword in query_lower:
            return True
    
    return False


def _is_unhelpful_answer(answer: str) -> bool:
    """Detect unhelpful answers"""
    if not answer or len(answer.strip()) < 30:
        return True
    
    unhelpful_phrases = [
        "couldn't find",
        "could not find",
        "i don't have",
        "no information",
        "not found",
        "मुझे जानकारी नहीं मिली",
        "mujhe jankari nahi mili",
        "मुझे documents में",
        "mujhe documents mein",
        "नहीं मिला",
        "nahi mila",
        "नहीं मिली",
        "nahi mili",
        "i couldn't find",
    ]
    
    answer_lower = answer.lower()
    matches = sum(1 for phrase in unhelpful_phrases if phrase in answer_lower)
    
    return matches > 0


def _get_no_results_message(language: str, query: str) -> str:
    """When no results found anywhere"""
    if language == 'hindi':
        return f"माफ कीजिए, मुझे '{query}' के बारे में कोई जानकारी नहीं मिली। कृपया अपना सवाल अलग तरीके से पूछें या ज़्यादा details दें।"
    elif language == 'hinglish':
        return f"Sorry, mujhe '{query}' ke baare mein koi information nahi mili. Please apna question alag tareeke se puchein ya zyada details dein."
    else:
        return f"Sorry, I couldn't find information about '{query}'. Please try rephrasing or provide more details."



# ═══════════════════════════════════════════════════════
# 🌊 STREAMING ENDPOINT
# ═══════════════════════════════════════════════════════

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
                    from app.services.query.retrieval_service import retriever
                    retrieved_chunks = await retriever.search(
                        query=clean_question,
                        top_k=request.top_k or 5,
                        similarity_threshold=0.25,
                        document_id=request.document_id,
                        use_reranking=True
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
# 🐛 DEBUG ENDPOINTS
# ═══════════════════════════════════════════════════════

@router.post("/debug/query", summary="Debug: See full pipeline")
async def debug_query(request: QueryRequest):
    """Debug endpoint - see entire pipeline"""
    try:
        clean_question = validate_query(request.question)
        
        from app.services.query.retrieval_service import retriever
        retrieved_chunks = await retriever.search(
            query=clean_question,
            top_k=10,
            similarity_threshold=0.15,
            use_reranking=True
        )
        
        from app.services.query.llm_service import llm_service
        context = llm_service._build_clean_context(retrieved_chunks[:5])
        
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
                    "vector_score": chunk['similarity_score'],
                    "rerank_score": chunk.get('rerank_score'),
                    "content": chunk['content'],
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


@router.get("/debug/document/{document_id}", summary="Debug: See document chunks")
async def debug_document(document_id: str):
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


@router.get("/debug/search-test", summary="Debug: Test search relevance")
async def debug_search_test(query: str, top_k: int = 10):
    try:
        from app.services.query.retrieval_service import retriever
        results = await retriever.search(
            query=query,
            top_k=top_k,
            similarity_threshold=0.1,
            use_reranking=True
        )
        
        return {
            "query": query,
            "total_results": len(results),
            "results": [
                {
                    "rank": i + 1,
                    "document": r['document_name'],
                    "page": r.get('page_number'),
                    "vector_score": r['similarity_score'],
                    "rerank_score": r.get('rerank_score'),
                    "content_preview": r['content'][:300],
                    "content_length": len(r['content']),
                }
                for i, r in enumerate(results)
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))