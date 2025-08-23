"""
Document management module for the RAG Chatbot Backend
"""
import os
import time
from fastapi import HTTPException, UploadFile, File
from .models import DocumentResponse, SystemStatsResponse
from .utils import (
    extract_text_from_file, 
    generate_document_id, 
    save_file_to_disk
)
from .document_store import document_store
from .config import ALLOWED_FILE_TYPES, API_KEY

async def get_all_documents():
    """Get all uploaded documents"""
    return document_store.get_all_documents()

async def get_documents_by_organization(organization_id: int):
    """Get documents for a specific organization"""
    return document_store.get_documents_by_organization(organization_id)

async def upload_document(file: UploadFile = File(...), organization_id: int = None):
    """Upload and process a document"""
    try:
        # Validate file type
        if file.content_type not in ALLOWED_FILE_TYPES:
            raise HTTPException(
                status_code=400, 
                detail=f"File type {file.content_type} not supported. Supported types: PDF, TXT, DOC, DOCX, CSV"
            )
        
        # Read file content
        content = await file.read()
        
        # Extract text content
        extracted_text = extract_text_from_file(content, file.content_type, file.filename)
        
        # Generate unique document ID
        doc_id = generate_document_id(file.filename)
        
        # Save file to disk
        file_path = save_file_to_disk(content, doc_id, file.filename)
        
        # Store document metadata
        doc_data = {
            "id": doc_id,
            "filename": file.filename,
            "original_filename": file.filename,
            "file_type": file.content_type,
            "file_size": len(content),
            "file_path": file_path,
            "processed": True,
            "chunk_count": max(1, len(extracted_text) // 1000),  # Rough estimate
            "content_preview": extracted_text[:200] if extracted_text else f"Uploaded {file.content_type} file",
            "extracted_text": extracted_text,  # Store full extracted text for search
            "uploaded_at": time.time(),
            "organization_id": organization_id  # Add organization ID
        }
        
        # Add to persistent document store
        document_store.add_document(doc_id, doc_data)
        
        # Add to vector database for semantic search
        if extracted_text:
            from .vector_db import vector_db
            vector_metadata = {
                "document_id": doc_id,
                "filename": file.filename,
                "file_type": file.content_type,
                "file_size": len(content),
                "uploaded_at": time.time(),
                "organization_id": organization_id  # Add organization ID to vector metadata
            }
            vector_db.add_document(doc_id, extracted_text, vector_metadata)
        
        return doc_data
        
    except Exception as e:
        print(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

async def delete_document(document_id: str):
    """Delete a document"""
    if not document_store.document_exists(document_id):
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc_data = document_store.get_document(document_id)
    
    # Remove file from disk if it exists
    try:
        if os.path.exists(doc_data["file_path"]):
            os.remove(doc_data["file_path"])
    except Exception as e:
        print(f"Error removing file: {e}")
    
    # Remove from persistent document store
    document_store.remove_document(document_id)
    
    # Remove from vector database
    from .vector_db import vector_db
    vector_db.delete_document(document_id)
    
    return {"message": "Document deleted successfully"}

async def get_system_stats() -> SystemStatsResponse:
    """Get system statistics"""
    total_docs = document_store.get_document_count()
    
    # Get vector database stats
    from .vector_db import vector_db
    vector_stats = vector_db.get_collection_stats()
    
    return SystemStatsResponse(
        total_documents=total_docs,
        total_chunks=vector_stats["total_chunks"],
        vector_db_status=vector_stats["status"],
        ai_configured=bool(API_KEY)
    )

async def get_organization_stats(organization_id: int) -> dict:
    """Get statistics for a specific organization"""
    org_docs = document_store.get_documents_by_organization(organization_id)
    
    return {
        "total_documents": len(org_docs),
        "organization_id": organization_id
    }
