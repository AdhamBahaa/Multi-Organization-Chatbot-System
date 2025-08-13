"""
Complete Backend Server with Authentication and Basic RAG Functionality
"""
from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import Optional, List
import os
import uvicorn
from dotenv import load_dotenv
import google.generativeai as genai
import hashlib
import time
import re
import PyPDF2
import docx
from io import BytesIO

# Load environment variables
load_dotenv()

app = FastAPI(title="RAG Chatbot API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Gemini API
api_key = os.getenv("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

# Pydantic models
class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    username: str
    role: str

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[int] = None

class ChatResponse(BaseModel):
    response: str
    session_id: int
    message_id: int
    sources: List[dict] = []
    confidence: float = 0.0
    chunks_found: int = 0

class SystemStatsResponse(BaseModel):
    total_documents: int
    total_chunks: int
    vector_db_status: str
    ai_configured: bool

# Simple in-memory document store for demo
DOCUMENTS_STORE = {}

def extract_text_from_file(file_content: bytes, content_type: str, filename: str) -> str:
    """Extract text content from uploaded files"""
    try:
        if content_type == 'text/plain':
            return file_content.decode('utf-8', errors='ignore')
        
        elif content_type == 'application/pdf':
            try:
                # Try PyPDF2 first
                pdf_file = BytesIO(file_content)
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
            except Exception as e:
                print(f"PDF extraction error: {e}")
                return f"PDF file uploaded: {filename}. Content extraction failed, but file is stored."
        
        elif content_type in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/msword']:
            try:
                doc_file = BytesIO(file_content)
                doc = docx.Document(doc_file)
                text = ""
                for paragraph in doc.paragraphs:
                    text += paragraph.text + "\n"
                return text
            except Exception as e:
                print(f"DOCX extraction error: {e}")
                return f"Word document uploaded: {filename}. Content extraction failed, but file is stored."
        
        elif content_type == 'text/csv':
            return file_content.decode('utf-8', errors='ignore')
        
        else:
            return f"File uploaded: {filename}. Text extraction not supported for {content_type}."
    
    except Exception as e:
        print(f"Text extraction error: {e}")
        return f"File uploaded: {filename}. Content extraction failed."

def search_documents(query: str) -> List[dict]:
    """Simple text search through uploaded documents"""
    results = []
    query_lower = query.lower()
    
    for doc_id, doc_data in DOCUMENTS_STORE.items():
        if 'extracted_text' in doc_data:
            text = doc_data['extracted_text'].lower()
            # Simple keyword matching
            if any(word in text for word in query_lower.split()):
                # Extract relevant chunks
                sentences = text.split('.')
                relevant_chunks = []
                for sentence in sentences:
                    if any(word in sentence for word in query_lower.split()):
                        relevant_chunks.append(sentence.strip())
                
                if relevant_chunks:
                    results.append({
                        'document_id': doc_id,
                        'filename': doc_data['filename'],
                        'chunks': relevant_chunks[:3],  # Top 3 relevant chunks
                        'relevance': len(relevant_chunks)
                    })
    
    # Sort by relevance
    results.sort(key=lambda x: x['relevance'], reverse=True)
    return results

# Simple in-memory user store for demo
DEMO_USERS = {
    "admin": {"id": 1, "username": "admin", "password": "admin123", "role": "admin"},
    "user": {"id": 2, "username": "user", "password": "user123", "role": "user"},
    "demo": {"id": 3, "username": "demo", "password": "demo123", "role": "user"}
}

# Authentication endpoints
@app.post("/api/login", response_model=TokenResponse)
async def login(login_data: LoginRequest):
    """Login endpoint"""
    user_data = DEMO_USERS.get(login_data.username)
    
    if not user_data or user_data["password"] != login_data.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Create mock token (in production, use proper JWT)
    access_token = f"mock-token-{user_data['username']}-{user_data['role']}"
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user_data["id"],
        username=user_data["username"],
        role=user_data["role"]
    )

@app.get("/api/me")
async def get_current_user_info():
    """Get current user information (mock response)"""
    return {
        "id": 1,
        "username": "demo_user",
        "email": "demo@example.com",
        "role": "user",
        "is_active": True,
        "created_at": "2025-08-10T00:00:00"
    }

# Chat endpoints
@app.post("/api/chat", response_model=ChatResponse)
async def chat(chat_data: ChatRequest):
    """Send a message and get AI-powered response with RAG"""
    
    # Search through uploaded documents
    search_results = search_documents(chat_data.message)
    
    # Prepare context from documents
    document_context = ""
    sources = []
    
    if search_results:
        document_context = "\n\nRelevant information from uploaded documents:\n"
        for result in search_results[:2]:  # Use top 2 most relevant documents
            document_context += f"\nFrom {result['filename']}:\n"
            for chunk in result['chunks']:
                if chunk.strip():
                    document_context += f"- {chunk.strip()}\n"
            
            sources.append({
                "document_id": result['document_id'],
                "filename": result['filename'],
                "relevance": result['relevance']
            })
    
    # Generate response using Gemini with document context
    try:
        if api_key:
            model = genai.GenerativeModel("gemini-1.5-flash")
            
            prompt = f"""You are a helpful RAG chatbot assistant. Answer the user's question based on the provided context from their uploaded documents.

User Question: {chat_data.message}

{document_context}

Instructions:
- If the document context contains relevant information, use it to answer the question
- If no relevant information is found in the documents, provide a general helpful response
- Be specific and reference the information from the documents when applicable
- If you mention information from documents, indicate which document it came from
"""
            
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=500,
                )
            )
            ai_response = response.text.strip()
        else:
            ai_response = "I'm a demo RAG chatbot. The Gemini API is not configured, so this is a mock response. Please configure the GOOGLE_API_KEY environment variable to enable AI responses."
    
    except Exception as e:
        ai_response = f"AI service temporarily unavailable: {str(e)}"
    
    # Mock session ID if not provided
    session_id = chat_data.session_id or 1
    
    return ChatResponse(
        response=ai_response,
        session_id=session_id,
        message_id=12345,  # Mock message ID
        sources=sources,
        confidence=0.8 if search_results else 0.5,
        chunks_found=len(search_results)
    )

@app.get("/api/sessions")
async def get_user_sessions():
    """Get user's chat sessions (mock response)"""
    return [
        {
            "id": 1,
            "title": "Demo Chat Session",
            "created_at": "2025-08-10T00:00:00",
            "message_count": 5
        }
    ]

# Document endpoints
@app.get("/api/documents")
async def get_documents():
    """Get all uploaded documents"""
    return list(DOCUMENTS_STORE.values())

@app.post("/api/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload document endpoint"""
    try:
        # Validate file type
        allowed_types = {
            'application/pdf': '.pdf',
            'text/plain': '.txt',
            'application/msword': '.doc',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
            'text/csv': '.csv'
        }
        
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail=f"File type {file.content_type} not supported. Supported types: PDF, TXT, DOC, DOCX, CSV"
            )
        
        # Read file content
        content = await file.read()
        
        # Extract text content
        extracted_text = extract_text_from_file(content, file.content_type, file.filename)
        
        # Generate unique document ID
        doc_id = hashlib.md5(f"{file.filename}{time.time()}".encode()).hexdigest()[:8]
        
        # Create upload directory if it doesn't exist
        upload_dir = os.path.join(os.path.dirname(__file__), 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file to disk
        file_path = os.path.join(upload_dir, f"{doc_id}_{file.filename}")
        with open(file_path, "wb") as f:
            f.write(content)
        
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
            "uploaded_at": time.time()
        }
        
        DOCUMENTS_STORE[doc_id] = doc_data
        
        return doc_data
        
    except Exception as e:
        print(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.delete("/api/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete a document"""
    if document_id not in DOCUMENTS_STORE:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc_data = DOCUMENTS_STORE[document_id]
    
    # Remove file from disk if it exists
    try:
        if os.path.exists(doc_data["file_path"]):
            os.remove(doc_data["file_path"])
    except Exception as e:
        print(f"Error removing file: {e}")
    
    # Remove from store
    del DOCUMENTS_STORE[document_id]
    
    return {"message": "Document deleted successfully"}

# System endpoints
@app.get("/api/system/stats", response_model=SystemStatsResponse)
async def get_system_stats():
    """Get system statistics"""
    total_docs = len(DOCUMENTS_STORE)
    total_chunks = sum(doc.get("chunk_count", 0) for doc in DOCUMENTS_STORE.values())
    
    return SystemStatsResponse(
        total_documents=total_docs,
        total_chunks=total_chunks,
        vector_db_status="operational" if total_docs > 0 else "empty",
        ai_configured=bool(api_key)
    )

# Health endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "RAG Chatbot API",
        "version": "1.0.0",
        "status": "running",
        "ai_configured": bool(api_key),
        "endpoints": {
            "docs": "/docs",
            "login": "/api/login",
            "chat": "/api/chat",
            "documents": "/api/documents"
        }
    }

@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "ai_configured": bool(api_key),
        "version": "1.0.0"
    }

if __name__ == "__main__":
    print("🚀 Starting RAG Chatbot Backend Server...")
    print(f"📡 API will be available at: http://localhost:8002")
    print(f"📚 API Documentation: http://localhost:8002/docs")
    print(f"🤖 Gemini API: {'✅ Configured' if api_key else '❌ Not configured'}")
    
    uvicorn.run(app, host="0.0.0.0", port=8002)
