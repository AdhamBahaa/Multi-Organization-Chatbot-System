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
from .config import CHUNKING_ENGINE, USE_VECTOR_DB, USE_GRAPH_DB
from .docling_chunker import chunk_text_with_docling
from .graph_db import graph_client
from .entity_extraction import extract_entities
from .document_store import document_store
from .config import ALLOWED_FILE_TYPES, BLOCKED_FILE_TYPES, API_KEY

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
            # chunk_count is derived from the selected chunking engine
            "chunk_count": 0,
            "content_preview": extracted_text[:200] if extracted_text else f"Uploaded {file.content_type} file",
            "extracted_text": extracted_text,  # Store full extracted text for search
            "uploaded_at": time.time(),
            "organization_id": organization_id  # Add organization ID
        }
        
        # Add to persistent document store
        document_store.add_document(doc_id, doc_data)
        
        # Chunk the document with the selected engine
        if extracted_text:
            if CHUNKING_ENGINE == "docling":
                chunks, used_engine = chunk_text_with_docling(file_path, extracted_text, max_chunk_size=1000)
                print(f"🧠 Chunking for '{file.filename}' done with engine: {used_engine}")
            else:
                # Fallback to previous simple sentence chunking alignment with vector_db
                from .vector_db import VectorDatabase
                chunks = VectorDatabase()._split_text_into_chunks(extracted_text, max_chunk_size=1000)
            doc_data["chunk_count"] = len(chunks)

            # Optionally index into vector DB (kept but gated)
            if USE_VECTOR_DB:
                try:
                    from .vector_db import vector_db
                    vector_metadata = {
                        "document_id": doc_id,
                        "filename": file.filename,
                        "file_type": file.content_type,
                        "file_size": len(content),
                        "uploaded_at": time.time(),
                        "organization_id": organization_id
                    }
                    vector_db.add_document(doc_id, extracted_text, vector_metadata)
                except Exception as e:
                    print(f"⚠️ Skipping vector DB indexing due to error: {e}")

            # Optionally write to graph DB
            if USE_GRAPH_DB:
                try:
                    # Upsert document
                    graph_client.upsert_document(doc_id, file.filename)
                    # Upsert chunks and relationships
                    for idx, chunk_text in enumerate(chunks):
                        chunk_id = f"{doc_id}_chunk_{idx}"
                        graph_client.upsert_chunk(doc_id, chunk_id, chunk_text, idx)
                        graph_client.relate_document_chunk(doc_id, chunk_id)
                        # Extract entities per chunk
                        entities_in_chunk = []
                        for ent_type, ent_name in extract_entities(chunk_text):
                            eid = graph_client.upsert_entity(ent_type, ent_name)
                            if eid:
                                entities_in_chunk.append((eid, ent_type, ent_name))
                                graph_client.relate_chunk_entity(chunk_id, eid)
                        # Create simple co-occurrence relationships among entities in the same chunk
                        try:
                            for i in range(len(entities_in_chunk)):
                                for j in range(i + 1, len(entities_in_chunk)):
                                    src_id, _, _ = entities_in_chunk[i]
                                    tgt_id, _, _ = entities_in_chunk[j]
                                    graph_client.relate_entity_entity(src_id, "CO_OCCURS_WITH", tgt_id)
                        except Exception:
                            pass
                except Exception as e:
                    print(f"⚠️ Graph DB write skipped due to error: {e}")
        
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
    
    # Debug: Print document details for this organization
    print(f"🔍 Organization {organization_id} stats:")
    print(f"   Total documents found: {len(org_docs)}")
    for i, doc in enumerate(org_docs):
        print(f"   Document {i+1}: {doc.get('filename', 'Unknown')} (ID: {doc.get('id', 'Unknown')})")
    
    # Return detailed information including document list
    return {
        "total_documents": len(org_docs),
        "organization_id": organization_id,
        "documents": [
            {
                "id": doc.get("id"),
                "filename": doc.get("filename"),
                "organization_id": doc.get("organization_id"),
                "has_extracted_text": bool(doc.get("extracted_text")),
                "text_length": len(doc.get("extracted_text", "")),
                "chunk_count": doc.get("chunk_count", 0)
            }
            for doc in org_docs
        ]
    }
