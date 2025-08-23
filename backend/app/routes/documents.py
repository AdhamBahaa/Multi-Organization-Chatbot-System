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
        from ..document_store import document_store
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
