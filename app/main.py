"""
FastAPI Main Application - Full RAG System
"""
import os
import hashlib
import uuid
import time
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional
from loguru import logger

from app.config import settings
from app.database.connection import db


UPLOAD_DIR = Path("./uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting RAG System...")
    await db.connect()
    logger.info("Database connected!")
    yield
    logger.info("Shutting down...")
    await db.disconnect()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan
)


# ─────────────────────────────────────
# MODELS
# ─────────────────────────────────────

class EmbedRequest(BaseModel):
    text: str

class SimilarityRequest(BaseModel):
    text1: str
    text2: str

class QueryRequest(BaseModel):
    question: str
    top_k: Optional[int] = 5
    document_id: Optional[str] = None
    temperature: Optional[float] = 0.3

class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5
    document_id: Optional[str] = None


# ─────────────────────────────────────
# BASIC ENDPOINTS
# ─────────────────────────────────────

@app.get("/")
async def root():
    return {
        "message": "RAG System Running!",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "endpoints": {
            "upload": "POST /upload/pdf",
            "query": "POST /query (THE MAIN RAG ENDPOINT)",
            "search": "POST /search",
            "documents": "GET /documents",
            "docs": "GET /docs (Swagger UI)"
        }
    }


@app.get("/health")
async def health():
    try:
        result = await db.fetchval("SELECT 1")
        db_status = "healthy" if result == 1 else "unhealthy"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "healthy",
        "database": db_status,
        "version": settings.APP_VERSION
    }


@app.get("/db-info")
async def db_info():
    try:
        tables = await db.fetch(
            "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename"
        )
        doc_count = await db.fetchval("SELECT COUNT(*) FROM documents")
        chunk_count = await db.fetchval("SELECT COUNT(*) FROM chunks")
        
        return {
            "tables": [t['tablename'] for t in tables],
            "documents_count": doc_count,
            "chunks_count": chunk_count
        }
    except Exception as e:
        return {"error": str(e)}


@app.get("/test-ollama")
async def test_ollama():
    """Test if Ollama is responding"""
    from app.services.query.llm_service import llm_service
    return await llm_service.test_ollama()


# ─────────────────────────────────────
# EMBEDDING ENDPOINTS
# ─────────────────────────────────────

@app.post("/embed/test")
async def test_embedding(request: EmbedRequest):
    try:
        from app.services.upload.embedder import embedder
        vector = embedder.embed_text(request.text)
        return {
            "text": request.text,
            "embedding_dimension": len(vector),
            "first_5_values": vector[:5]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/embed/similarity")
async def test_similarity(request: SimilarityRequest):
    try:
        from app.services.upload.embedder import embedder
        vec1 = embedder.embed_text(request.text1)
        vec2 = embedder.embed_text(request.text2)
        similarity = embedder.cosine_similarity(vec1, vec2)
        
        return {
            "text1": request.text1,
            "text2": request.text2,
            "similarity_score": round(similarity, 4)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────
# UPLOAD PIPELINE
# ─────────────────────────────────────

@app.post("/upload/pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """Upload PDF and process it (extract → chunk → embed → store)"""
    try:
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(400, "Only PDF files supported")
        
        contents = await file.read()
        file_size = len(contents)
        
        if file_size > settings.MAX_PDF_SIZE:
            raise HTTPException(400, f"File too large")
        
        file_hash = hashlib.sha256(contents).hexdigest()
        
        existing = await db.fetchrow(
            "SELECT id, original_name FROM documents WHERE file_hash = $1",
            file_hash
        )
        if existing:
            return {
                "status": "duplicate",
                "message": "Already uploaded",
                "document_id": str(existing['id'])
            }
        
        file_path = UPLOAD_DIR / f"{file_hash}.pdf"
        with open(file_path, 'wb') as f:
            f.write(contents)
        
        from app.services.upload.pdf_extractor import pdf_extractor
        extraction = pdf_extractor.extract_text(str(file_path))
        
        if not extraction['full_text']:
            raise HTTPException(400, "No text in PDF")
        
        doc_id = await db.fetchval("""
            INSERT INTO documents (
                original_name, file_type, mime_type, file_size, 
                file_hash, page_count, word_count, status
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id
        """, 
            file.filename, "pdf", "application/pdf", file_size,
            file_hash, extraction['total_pages'],
            len(extraction['full_text'].split()), "processing"
        )
        
        from app.services.upload.chunker import chunker
        chunks = chunker.chunk_pages(extraction['pages'])
        
        from app.services.upload.embedder import embedder
        texts = [c['content'] for c in chunks]
        embeddings = embedder.embed_batch(texts)
        
        saved_count = 0
        for chunk, embedding in zip(chunks, embeddings):
            try:
                content_hash = hashlib.sha256(chunk['content'].encode()).hexdigest()
                vector_str = "[" + ",".join(map(str, embedding)) + "]"
                
                await db.execute("""
                    INSERT INTO chunks (
                        document_id, content, content_hash, embedding,
                        chunk_index, page_number, token_count, chunk_type
                    ) VALUES ($1, $2, $3, $4::vector, $5, $6, $7, $8)
                    ON CONFLICT (document_id, content_hash) DO NOTHING
                """,
                    doc_id, chunk['content'], content_hash, vector_str,
                    chunk['chunk_index'], chunk.get('page_number'),
                    chunk['token_count'], 'text'
                )
                saved_count += 1
            except Exception as e:
                logger.error(f"Chunk save failed: {e}")
        
        await db.execute(
            "UPDATE documents SET status = 'completed', processed_at = NOW() WHERE id = $1",
            doc_id
        )
        
        return {
            "status": "success",
            "document_id": str(doc_id),
            "filename": file.filename,
            "pages": extraction['total_pages'],
            "chunks_saved": saved_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────
# 🔍 SEARCH ENDPOINT (Retrieval only)
# ─────────────────────────────────────

@app.post("/search")
async def search_chunks(request: SearchRequest):
    """
    Search for relevant chunks (no LLM, just retrieval)
    Useful for debugging
    """
    try:
        from app.services.query.retrieval_service import retriever
        
        results = await retriever.search(
            query=request.query,
            top_k=request.top_k,
            document_id=request.document_id
        )
        
        return {
            "query": request.query,
            "total_results": len(results),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────
# 🤖 QUERY ENDPOINT (THE MAIN RAG!)
# ─────────────────────────────────────

@app.post("/query")
async def query_rag(request: QueryRequest):
    """
    🎯 MAIN RAG ENDPOINT
    
    Ask a question, get an answer based on uploaded documents.
    
    Pipeline:
    1. Embed question
    2. Search relevant chunks (vector similarity)
    3. Build context from chunks
    4. Generate answer using Ollama LLM
    5. Return answer with sources
    """
    start_time = time.time()
    
    try:
        from app.services.query.retrieval_service import retriever
        from app.services.query.llm_service import llm_service
        
        # Step 1: Retrieve relevant chunks
        logger.info(f"📥 Query received: '{request.question}'")
        
        retrieval_start = time.time()
        chunks = await retriever.search(
            query=request.question,
            top_k=request.top_k,
            document_id=request.document_id
        )
        retrieval_time = (time.time() - retrieval_start) * 1000
        
        if not chunks:
            return {
                "answer": "I couldn't find any relevant information. Please upload documents first.",
                "sources": [],
                "stats": {
                    "chunks_found": 0,
                    "total_time_ms": int((time.time() - start_time) * 1000)
                }
            }
        
        # Step 2: Generate answer
        llm_start = time.time()
        result = await llm_service.generate_answer(
            query=request.question,
            context_chunks=chunks,
            temperature=request.temperature
        )
        llm_time = (time.time() - llm_start) * 1000
        
        total_time = (time.time() - start_time) * 1000
        
        return {
            "question": request.question,
            "answer": result['answer'],
            "sources": result['sources'],
            "stats": {
                "chunks_found": len(chunks),
                "model": result['model'],
                "tokens_used": result['tokens_used'],
                "retrieval_time_ms": int(retrieval_time),
                "llm_time_ms": int(llm_time),
                "total_time_ms": int(total_time)
            }
        }
        
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────
# DOCUMENT MANAGEMENT
# ─────────────────────────────────────

@app.get("/documents")
async def list_documents():
    try:
        docs = await db.fetch("""
            SELECT 
                d.id, d.original_name, d.file_size, d.page_count,
                d.status, d.created_at,
                COUNT(c.id) as chunk_count
            FROM documents d
            LEFT JOIN chunks c ON c.document_id = d.id
            GROUP BY d.id
            ORDER BY d.created_at DESC
        """)
        
        return {
            "total": len(docs),
            "documents": [
                {
                    "id": str(d['id']),
                    "name": d['original_name'],
                    "size_kb": d['file_size'] // 1024 if d['file_size'] else 0,
                    "pages": d['page_count'],
                    "chunks": d['chunk_count'],
                    "status": d['status'],
                    "uploaded_at": d['created_at'].isoformat() if d['created_at'] else None
                }
                for d in docs
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    try:
        await db.execute(
            "DELETE FROM documents WHERE id = $1",
            uuid.UUID(document_id)
        )
        return {"status": "deleted", "document_id": document_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
