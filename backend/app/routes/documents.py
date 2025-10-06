"""
Document management routes for the RAG Chatbot Backend
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import Union, List
from ..database import get_db, Admin, User
from ..auth import get_current_user
from ..documents import get_all_documents, get_documents_by_organization, upload_document, delete_document, get_organization_stats
from ..models import DocumentResponse, SystemStatsResponse
from ..document_store import document_store
from ..config import USE_VECTOR_DB

router = APIRouter(prefix="/documents", tags=["Documents"])

@router.get("", response_model=List[DocumentResponse])
async def get_documents(
    current_user: Union[Admin, User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get documents for the current user's organization"""
    try:
        # Get organization ID from current user
        if isinstance(current_user, Admin):
            organization_id = current_user.OrganizationID
        else:  # User
            organization_id = current_user.OrganizationID
        
        # Get documents for this organization only
        documents = await get_documents_by_organization(organization_id)
        return documents
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get documents: {str(e)}"
        )

@router.post("/upload", response_model=DocumentResponse)
async def upload_document_endpoint(
    file: UploadFile = File(...),
    current_user: Union[Admin, User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload and process a document"""
    try:
        # Get organization ID from current user
        if isinstance(current_user, Admin):
            organization_id = current_user.OrganizationID
        else:  # User
            organization_id = current_user.OrganizationID
        
        result = await upload_document(file, organization_id)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {str(e)}"
        )

@router.delete("/{document_id}")
async def delete_document_endpoint(
    document_id: str,
    current_user: Union[Admin, User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a document"""
    try:
        # Get organization ID from current user
        if isinstance(current_user, Admin):
            organization_id = current_user.OrganizationID
        else:  # User
            organization_id = current_user.OrganizationID
        
        # Check if document belongs to user's organization
        doc_data = document_store.get_document(document_id)
        if not doc_data:
            raise HTTPException(status_code=404, detail="Document not found")
        
        if doc_data.get('organization_id') != organization_id:
            raise HTTPException(status_code=403, detail="Access denied: Document belongs to different organization")
        
        result = await delete_document(document_id)
        return {"message": "Document deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Delete failed: {str(e)}"
        )

@router.get("/stats/organization")
async def get_organization_document_stats(
    current_user: Union[Admin, User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get document statistics for the current user's organization"""
    try:
        # Get organization ID from current user
        if isinstance(current_user, Admin):
            organization_id = current_user.OrganizationID
        else:  # User
            organization_id = current_user.OrganizationID
        
        stats = await get_organization_stats(organization_id)
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get organization stats: {str(e)}"
        )

@router.get("/debug/organization")
async def debug_organization_documents(
    current_user: Union[Admin, User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Debug endpoint to check organization filtering"""
    try:
        # Get organization ID from current user
        if isinstance(current_user, Admin):
            organization_id = current_user.OrganizationID
            user_type = "Admin"
        else:  # User
            organization_id = current_user.OrganizationID
            user_type = "User"
        
        # Get documents for this organization
        org_docs = document_store.get_documents_by_organization(organization_id)
        
        # Get all documents for comparison
        all_docs = document_store.get_all_documents()
        
        return {
            "user_info": {
                "user_type": user_type,
                "user_id": current_user.ID,
                "organization_id": organization_id
            },
            "organization_documents": {
                "count": len(org_docs),
                "documents": [
                    {
                        "id": doc.get("id"),
                        "filename": doc.get("filename"),
                        "organization_id": doc.get("organization_id"),
                        "uploaded_at": doc.get("uploaded_at")
                    }
                    for doc in org_docs
                ]
            },
            "all_documents": {
                "count": len(all_docs),
                "documents": [
                    {
                        "id": doc.get("id"),
                        "filename": doc.get("filename"),
                        "organization_id": doc.get("organization_id"),
                        "uploaded_at": doc.get("uploaded_at")
                    }
                    for doc in all_docs
                ]
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Debug failed: {str(e)}"
        )


@router.post("/reindex")
async def reindex_documents(
    current_user: Union[Admin, User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """(Re)index all documents for the current user's organization into the vector DB.

    - Deletes existing embeddings per document to avoid duplicates
    - Adds fresh embeddings using the current Docling/simple pipeline in vector_db
    """
    if not USE_VECTOR_DB:
        raise HTTPException(status_code=400, detail="Vector DB is disabled by configuration")

    try:
        # Determine organization
        organization_id = current_user.OrganizationID

        # Collect documents for this org
        org_docs = document_store.get_documents_by_organization(organization_id)
        if not org_docs:
            return {"message": "No documents to index", "indexed": 0, "skipped": 0}

        from ..vector_db import vector_db
        indexed = 0
        skipped = 0
        for doc in org_docs:
            doc_id = doc.get("id")
            text = doc.get("extracted_text") or ""
            if not doc_id or not text:
                skipped += 1
                continue

            # Remove previous embeddings for this doc
            try:
                vector_db.delete_document(doc_id)
            except Exception:
                pass

            # Add fresh embeddings
            metadata = {
                "document_id": doc_id,
                "filename": doc.get("filename", ""),
                "file_type": doc.get("file_type", ""),
                "file_size": doc.get("file_size", 0),
                "uploaded_at": doc.get("uploaded_at", 0),
                "organization_id": organization_id,
            }
            ok = vector_db.add_document(doc_id, text, metadata)
            if ok:
                indexed += 1
            else:
                skipped += 1

        return {
            "message": "Reindex completed",
            "indexed": indexed,
            "skipped": skipped,
            "organization_id": organization_id,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reindex failed: {str(e)}")


@router.get("/{document_id}/chunks")
async def get_document_chunks(
    document_id: str,
    engine: str = "docling",
    current_user: Union[Admin, User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Return chunks for a given document using the selected chunking engine (default: docling)."""
    try:
        # Ensure document exists and belongs to user's organization
        doc = document_store.get_document(document_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        user_org_id = current_user.OrganizationID
        if doc.get("organization_id") != user_org_id:
            raise HTTPException(status_code=403, detail="Access denied: Document belongs to different organization")

        extracted_text = doc.get("extracted_text") or ""
        if not extracted_text:
            # Attempt to recover text from the stored file on disk after a restart
            try:
                import os
                file_path = doc.get("file_path", "")
                content_type = doc.get("file_type", "")
                filename = doc.get("filename", "")
                if file_path and os.path.exists(file_path):
                    with open(file_path, "rb") as f:
                        content = f.read()
                    from ..utils import extract_text_from_file
                    recovered = extract_text_from_file(content, content_type, filename) or ""
                    # If extractor returned a descriptive placeholder, treat as empty
                    if recovered and not recovered.lower().startswith(("file uploaded", "pdf file uploaded", "word document uploaded")):
                        extracted_text = recovered
                        # Persist the recovered text back into the registry
                        try:
                            doc["extracted_text"] = extracted_text
                            document_store.add_document(document_id, doc)
                        except Exception:
                            pass
            except Exception:
                pass
        if not extracted_text:
            return {"document_id": document_id, "engine": engine, "chunks": [], "chunk_count": 0}

        # Choose engine
        chunks = []
        used_engine = engine
        if engine in ("docling", "docling-hybrid", "docling-hierarchical"):
            try:
                from ..docling_chunker import (
                    chunk_text_with_docling_with_debug_info,
                    chunk_text_with_docling_debug,
                    simple_sentence_chunk,
                )
                # Pass both pdf_path and text to the docling chunker (correct signature)
                pdf_path = doc.get("file_path", "")
                # Pass prefer_hybrid override when engine=docling-hybrid or docling-hierarchical
                prefer_hybrid = True if engine == "docling-hybrid" else (False if engine == "docling-hierarchical" else None)
                chunks, used_engine, debug_info = chunk_text_with_docling_with_debug_info(
                    pdf_path=pdf_path, text=extracted_text, max_chunk_size=1000, prefer_hybrid=prefer_hybrid
                )
            except Exception as e:
                # Route-level log to help diagnose silent fallback
                print(f"[chunks-route] Docling failed, falling back to simple. Error: {e}")
                from ..docling_chunker import simple_sentence_chunk
                chunks = simple_sentence_chunk(extracted_text, max_chunk_size=1000)
                used_engine = "simple"
                debug_info = {"error": str(e)}
        else:
            from ..docling_chunker import simple_sentence_chunk
            chunks = simple_sentence_chunk(extracted_text, max_chunk_size=1000)
            used_engine = "simple"
            debug_info = {"note": "simple engine selected"}

        resp = {
            "document_id": document_id,
            "engine": engine,
            "used_engine": used_engine,
            "chunk_count": len(chunks),
            "chunks": chunks,
            "filename": doc.get("filename"),
            "debug": debug_info,
        }
        # Route-level log for visibility
        print(f"[chunks-route] document_id={document_id} requested_engine={engine} used_engine={used_engine} chunks={len(chunks)}")
        return resp
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get chunks: {str(e)}")
