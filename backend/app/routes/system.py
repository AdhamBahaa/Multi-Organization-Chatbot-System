"""
System and utility routes
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Union
from ..database import get_db, Admin, User
from ..auth import get_current_user
from ..vector_db import vector_db
from ..document_store import document_store
from ..config import API_KEY
from ..models import SystemStatsResponse

router = APIRouter(prefix="/system", tags=["System"])

@router.get("/stats", response_model=SystemStatsResponse)
async def get_system_stats(
    current_user: Union[Admin, User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get system statistics"""
    try:
        # Get document count
        total_documents = document_store.get_document_count()
        
        # Get vector database stats
        vector_stats = vector_db.get_collection_stats()
        vector_db_status = "healthy" if vector_stats.get('status') != 'error' else "error"
        
        # Get total chunks (approximate)
        total_chunks = sum(doc.get('chunk_count', 0) for doc in document_store.get_all_documents())
        
        return SystemStatsResponse(
            total_documents=total_documents,
            total_chunks=total_chunks,
            vector_db_status=vector_db_status,
            ai_configured=bool(API_KEY)
        )
    except Exception as e:
        return SystemStatsResponse(
            total_documents=0,
            total_chunks=0,
            vector_db_status="error",
            ai_configured=bool(API_KEY)
        )

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "System is running"}

@router.get("/debug/documents")
async def debug_documents():
    """Debug endpoint to check document store and vector database"""
    from ..document_store import document_store
    from ..vector_db import vector_db
    
    # Get document store info
    all_docs = document_store.get_all_documents()
    doc_count = document_store.get_document_count()
    
    # Get vector database info
    vector_stats = vector_db.get_collection_stats()
    
    # Check if documents have extracted text
    docs_with_text = 0
    for doc in all_docs:
        if 'extracted_text' in doc and doc['extracted_text']:
            docs_with_text += 1
    
    return {
        "document_store": {
            "total_documents": doc_count,
            "documents_with_text": docs_with_text,
            "documents": [
                {
                    "id": doc.get("id"),
                    "filename": doc.get("filename"),
                    "has_extracted_text": 'extracted_text' in doc and bool(doc['extracted_text']),
                    "text_length": len(doc.get('extracted_text', ''))
                }
                for doc in all_docs[:5]  # Show first 5 documents
            ]
        },
        "vector_database": vector_stats
    }

@router.get("/debug/search/{query}")
async def debug_search(query: str):
    """Debug endpoint to test document search"""
    from ..utils import search_documents
    
    results = search_documents(query)
    
    return {
        "query": query,
        "results_count": len(results),
        "results": results
    }
