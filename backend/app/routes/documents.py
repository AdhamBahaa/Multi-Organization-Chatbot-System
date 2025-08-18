"""
Document management routes for the RAG Chatbot Backend
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import Union, List
from ..database import get_db, Admin, User
from ..auth import get_current_user
from ..documents import get_all_documents, upload_document, delete_document
from ..models import DocumentResponse, SystemStatsResponse

router = APIRouter(prefix="/documents", tags=["Documents"])

@router.get("", response_model=List[DocumentResponse])
async def get_documents(
    current_user: Union[Admin, User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all uploaded documents"""
    try:
        documents = await get_all_documents()
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
        result = await upload_document(file)
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
        result = await delete_document(document_id)
        return {"message": "Document deleted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Delete failed: {str(e)}"
        )
