"""
Document Management Endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.database import documents
from app.models import (
    DocumentListResponse, DocumentInfo, DocumentDeleteResponse
)
from app.utils import (
    logger, is_valid_uuid, format_file_size, to_iso_string,
    NotFoundError, ValidationError
)

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.get("", response_model=DocumentListResponse, summary="List all documents")
async def list_documents(
    status: Optional[str] = Query(None, description="Filter by status"),
    file_type: Optional[str] = Query(None, description="Filter by file type"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """
    List uploaded documents with optional filters.
    
    Returns documents with their chunk counts.
    """
    try:
        docs = await documents.list_documents(
            limit=limit,
            offset=offset,
            status=status,
            file_type=file_type
        )
        
        document_list = [
            DocumentInfo(
                id=str(d['id']),
                name=d['original_name'],
                file_type=d.get('file_type'),
                size_bytes=d['file_size'] or 0,
                size_readable=format_file_size(d['file_size'] or 0),
                pages=d.get('page_count'),
                chunks=d.get('chunk_count', 0),
                status=d['status'],
                language=d.get('language'),
                uploaded_at=to_iso_string(d.get('created_at')),
                processed_at=to_iso_string(d.get('processed_at'))
            )
            for d in docs
        ]
        
        total = await documents.count_documents(status=status)
        
        return DocumentListResponse(
            total=total,
            documents=document_list
        )
        
    except Exception as e:
        logger.error(f"List documents failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}", response_model=DocumentInfo, summary="Get document by ID")
async def get_document(document_id: str):
    """Get details of a specific document"""
    try:
        if not is_valid_uuid(document_id):
            raise ValidationError("Invalid document ID format").to_http_exception()
        
        doc = await documents.get_by_id(document_id)
        
        if not doc:
            raise NotFoundError("Document", document_id).to_http_exception()
        
        return DocumentInfo(
            id=str(doc['id']),
            name=doc['original_name'],
            file_type=doc.get('file_type'),
            size_bytes=doc['file_size'] or 0,
            size_readable=format_file_size(doc['file_size'] or 0),
            pages=doc.get('page_count'),
            chunks=0,  # Could fetch separately
            status=doc['status'],
            language=doc.get('language'),
            uploaded_at=to_iso_string(doc.get('created_at')),
            processed_at=to_iso_string(doc.get('processed_at'))
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get document failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{document_id}", response_model=DocumentDeleteResponse, summary="Delete document")
async def delete_document(document_id: str):
    """
    Delete a document and all its chunks (CASCADE).
    This action cannot be undone!
    """
    try:
        if not is_valid_uuid(document_id):
            raise ValidationError("Invalid document ID format").to_http_exception()
        
        # Check exists
        doc = await documents.get_by_id(document_id)
        if not doc:
            raise NotFoundError("Document", document_id).to_http_exception()
        
        # Delete
        deleted = await documents.delete_document(document_id)
        
        if not deleted:
            raise HTTPException(500, "Failed to delete document")
        
        return DocumentDeleteResponse(
            document_id=document_id,
            message=f"Document '{doc['original_name']}' deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete document failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
