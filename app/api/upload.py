"""
Document Upload Endpoints
"""
import time
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException

from app.config import settings
from app.database import documents, chunks
from app.models import UploadResponse
from app.utils import (
    logger, generate_file_hash, format_file_size,
    sanitize_filename, get_file_extension,
    FileTooLargeError, InvalidFileTypeError, ExtractionError,
    Messages
)

router = APIRouter(prefix="/upload", tags=["Upload"])

# Upload directory
UPLOAD_DIR = Path("./uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/pdf", response_model=UploadResponse, summary="Upload PDF document")
async def upload_pdf(file: UploadFile = File(..., description="PDF file to upload")):
    """
    Upload and process a PDF document:
    
    Pipeline:
    1. Validate file (type, size)
    2. Check for duplicates (SHA-256 hash)
    3. Save file to disk
    4. Extract text (PyMuPDF)
    5. Chunk text intelligently
    6. Generate embeddings (BGE-M3)
    7. Store in PostgreSQL with pgvector
    
    Returns processing stats and document ID.
    """
    start_time = time.time()
    
    try:
        # ─── VALIDATE FILE ───
        if not file.filename:
            raise HTTPException(400, "No filename provided")
        
        filename = sanitize_filename(file.filename)
        ext = get_file_extension(filename)
        
        if ext != "pdf":
            raise InvalidFileTypeError(ext, ["pdf"]).to_http_exception()
        
        # ─── READ FILE ───
        contents = await file.read()
        file_size = len(contents)
        
        if file_size == 0:
            raise HTTPException(400, "Empty file")
        
        if file_size > settings.MAX_PDF_SIZE:
            raise FileTooLargeError(file_size, settings.MAX_PDF_SIZE).to_http_exception()
        
        # ─── CHECK DUPLICATE ───
        file_hash = generate_file_hash(contents)
        existing = await documents.get_by_hash(file_hash)
        
        if existing:
            logger.info(f"Duplicate file detected: {filename}")
            return UploadResponse(
                status="duplicate",
                document_id=str(existing['id']),
                filename=filename,
                file_size=file_size,
                file_size_readable=format_file_size(file_size),
                chunks_created=0,
                chunks_saved=0,
                message=f"Already uploaded as: {existing['original_name']}"
            )
        
        # ─── SAVE FILE ───
        file_path = UPLOAD_DIR / f"{file_hash}.pdf"
        with open(file_path, 'wb') as f:
            f.write(contents)
        
        logger.info(f"File saved: {filename} ({format_file_size(file_size)})")
        
        # ─── EXTRACT TEXT ───
        from app.services.upload.pdf_extractor import pdf_extractor
        
        try:
            extraction = pdf_extractor.extract_text(str(file_path))
        except Exception as e:
            logger.error(f"PDF extraction failed: {e}")
            raise ExtractionError("PDF", str(e)).to_http_exception()
        
        if not extraction['full_text']:
            raise HTTPException(400, "PDF contains no extractable text (might be scanned)")
        
        # ─── CREATE DOCUMENT RECORD ───
        from app.utils import word_count
        
        doc_id = await documents.create_document(
            original_name=filename,
            file_type="pdf",
            mime_type="application/pdf",
            file_size=file_size,
            file_hash=file_hash,
            page_count=extraction['total_pages'],
            word_count=word_count(extraction['full_text']),
            status="processing"
        )
        
        # ─── CHUNK TEXT ───
        from app.services.upload.chunker import chunker
        
        text_chunks = chunker.chunk_pages(extraction['pages'])
        
        if not text_chunks:
            await documents.update_status(doc_id, "failed", error_message="No chunks created")
            raise HTTPException(400, "Failed to create chunks from PDF")
        
        # ─── GENERATE EMBEDDINGS (BATCH) ───
        from app.services.upload.embedder import embedder
        
        logger.info(f"Generating embeddings for {len(text_chunks)} chunks...")
        texts = [c['content'] for c in text_chunks]
        embeddings = embedder.embed_batch(texts)
        
        # ─── SAVE CHUNKS TO DATABASE ───
        saved_count = await chunks.insert_chunks_batch(doc_id, text_chunks, embeddings)
        
        # ─── UPDATE DOCUMENT STATUS ───
        processing_time = time.time() - start_time
        await documents.update_status(
            doc_id,
            "completed",
            processing_time=processing_time
        )
        
        logger.info(f"Document processed: {filename} in {processing_time:.2f}s")
        
        return UploadResponse(
            status="success",
            document_id=doc_id,
            filename=filename,
            file_size=file_size,
            file_size_readable=format_file_size(file_size),
            pages=extraction['total_pages'],
            characters=extraction['total_characters'],
            chunks_created=len(text_chunks),
            chunks_saved=saved_count,
            processing_time_ms=int(processing_time * 1000),
            message=f"PDF processed successfully! {saved_count} chunks indexed."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
