"""
Main FastAPI application for the RAG Chatbot Backend
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import CORS_ORIGINS, API_KEY, API_HOST, API_PORT, DEV_MODE
from app.routes import router
from app.chat import configure_gemini

# Create FastAPI app
app = FastAPI(title="RAG Chatbot API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)

# Configure Gemini API and initialize databases on startup
@app.on_event("startup")
async def startup_event():
    configure_gemini()
    
    # Initialize vector database
    from app.vector_db import vector_db
    print(f"🗄️  Vector Database: {'✅ Initialized' if vector_db.get_collection_stats()['status'] != 'error' else '❌ Error'}")
    
    # Initialize document store (loads existing documents)
    from app.document_store import document_store
    print(f"📚 Document Store: ✅ Loaded {document_store.get_document_count()} documents")
    
    # Run cleanup to ensure data consistency
    from app.cleanup import cleanup_invalid_registry_entries
    cleanup_invalid_registry_entries()

if __name__ == "__main__":
    print("🚀 Starting RAG Chatbot Backend Server...")
    print(f"📡 API will be available at: http://localhost:{API_PORT}")
    print(f"📚 API Documentation: http://localhost:{API_PORT}/docs")
    print(f"🤖 Gemini API: {'✅ Configured' if API_KEY else '❌ Not configured'}")
    print("👥 Development Mode: 🔗 Shared (Team Collaboration)")
    
    uvicorn.run(app, host=API_HOST, port=API_PORT)
