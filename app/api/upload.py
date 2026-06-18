"""
Universal Document Upload Endpoints
Supports: PDF, DOCX, XLSX, CSV, TXT, HTML, MD
"""
import time
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException

from app.config import settings
from app.database import documents, chunks
from app.models import UploadResponse
from app.utils import (
    logger, generate_file_hash, format_file_size,
    sanitize_filename, word_count,
    FileTooLargeError, InvalidFileTypeError, ExtractionError
)
from app.services.upload.file_detector import file_detector
from app.services.upload.document_processor import document_processor

router = APIRouter(prefix="/upload", tags=["Upload"])

# Upload directory
UPLOAD_DIR = Path("./uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.get("/supported-types", summary="List supported file types")
async def get_supported_types():
    """Get all supported file types and their limits"""
    return {
        "supported_types": file_detector.get_supported_types(),
        "categories": ["document", "spreadsheet", "text", "image"],
        "total_types": len(file_detector.SUPPORTED_TYPES)
    }


@router.post("", response_model=UploadResponse, summary="Universal document upload")
async def upload_document(file: UploadFile = File(..., description="Any supported document")):
    """
    ## Universal Document Upload
    
    Upload any supported document type. Auto-detects format and processes accordingly.
    
    ### Supported Formats:
    - **Documents**: PDF, DOCX, DOC
    - **Spreadsheets**: XLSX, XLS, CSV
    - **Text**: TXT, HTML, MD
    - **Images**: JPG, PNG (coming with OCR in Phase 3)
    
    ### Pipeline:
    1. Detect file type (extension + magic bytes + MIME)
    2. Validate size against type limits
    3. Check for duplicates (SHA-256 hash)
    4. Save file
    5. Extract text using appropriate parser
    6. Chunk text intelligently
    7. Generate embeddings (BGE-M3)
    8. Store in PostgreSQL with pgvector
    """
    start_time = time.time()
    
    try:
        # ─── VALIDATE INPUT ───
        if not file.filename:
            raise HTTPException(400, "No filename provided")
        
        filename = sanitize_filename(file.filename)
        
        # ─── READ FILE ───
        contents = await file.read()
        file_size = len(contents)
        
        if file_size == 0:
            raise HTTPException(400, "Empty file")
        
        # ─── DETECT FILE TYPE ───
        try:
            detection = file_detector.detect(
                filename=filename,
                content=contents,
                provided_mime=file.content_type
            )
        except InvalidFileTypeError as e:
            raise e.to_http_exception()
        
        file_type = detection['file_type']
        mime_type = detection['mime_type']
        max_size = detection['max_size_bytes']
        
        logger.info(
            f"Upload: {filename} ({format_file_size(file_size)}) "
            f"detected as {file_type}"
        )
        
        # ─── VALIDATE SIZE ───
        if file_size > max_size:
            raise FileTooLargeError(file_size, max_size).to_http_exception()
        
        # ─── CHECK DUPLICATE ───
        file_hash = generate_file_hash(contents)
        existing = await documents.get_by_hash(file_hash)
        
        if existing:
            logger.info(f"Duplicate file: {filename}")
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
        ext = detection['extension']
        file_path = UPLOAD_DIR / f"{file_hash}.{ext}"
        with open(file_path, 'wb') as f:
            f.write(contents)
        
        logger.info(f"File saved: {file_path.name}")
        
        # ─── EXTRACT CONTENT ───
        try:
            extraction = document_processor.process(str(file_path), file_type)
        except ExtractionError as e:
            raise e.to_http_exception()
        
        if not extraction['full_text'] or len(extraction['full_text'].strip()) < 10:
            raise HTTPException(
                400,
                f"Could not extract meaningful text from {file_type.upper()} file"
            )
        
        # ─── CREATE DOCUMENT RECORD ───
        doc_id = await documents.create_document(
            original_name=filename,
            file_type=file_type,
            mime_type=mime_type,
            file_size=file_size,
            file_hash=file_hash,
            page_count=extraction['total_pages'],
            word_count=word_count(extraction['full_text']),
            status="processing"
        )
        
        # ─── CHUNK TEXT ───
        from app.services.upload.chunker import chunker
        
        # Use page-based chunking if available
        if extraction.get('pages') and extraction.get('has_pages'):
            text_chunks = chunker.chunk_pages(extraction['pages'])
        else:
            # For single-page docs (DOCX, TXT, HTML)
            text_chunks = chunker.chunk_text(
                extraction['full_text'],
                metadata={'extraction_type': extraction['extraction_type']}
            )
            # Add chunk indices
            for i, chunk in enumerate(text_chunks):
                chunk['chunk_index'] = i
        
        if not text_chunks:
            await documents.update_status(doc_id, "failed", error_message="No chunks created")
            raise HTTPException(400, "Failed to create chunks")
        
        # ─── GENERATE EMBEDDINGS ───
        from app.services.upload.embedder import embedder
        
        logger.info(f"Generating embeddings for {len(text_chunks)} chunks...")
        texts = [c['content'] for c in text_chunks]
        embeddings = embedder.embed_batch(texts)
        
        # ─── SAVE CHUNKS ───
        saved_count = await chunks.insert_chunks_batch(doc_id, text_chunks, embeddings)
        
        # ─── UPDATE STATUS ───
        processing_time = time.time() - start_time
        await documents.update_status(
            doc_id,
            "completed",
            processing_time=processing_time
        )
        
        logger.info(
            f"Document processed: {filename} ({file_type}) in {processing_time:.2f}s, "
            f"{saved_count} chunks"
        )
        
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
            message=f"{file_type.upper()} processed successfully! {saved_count} chunks indexed."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


# Keep old endpoint for backward compatibility
@router.post("/pdf", response_model=UploadResponse, summary="Upload PDF (legacy)", deprecated=True)
async def upload_pdf(file: UploadFile = File(...)):
    """
    Legacy PDF-only endpoint.
    Use POST /upload instead (supports all formats).
    """
    return await upload_document(file)
