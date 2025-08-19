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
app.include_router(router, prefix="/api")

# Configure Gemini API and initialize databases on startup
@app.on_event("startup")
async def startup_event():
    # Check database connectivity (tables already exist)
    try:
        from app.database import engine
        with engine.connect() as conn:
            print("🗄️  Database: ✅ Connected to existing database")
    except Exception as e:
        print(f"🗄️  Database: ❌ Connection failed - {e}")
        print("   Make sure SQL Server is running and database 'chatbot' exists")
    
    configure_gemini()
    
    # Initialize vector database
    try:
        from app.vector_db import vector_db
        print(f"🗄️  Vector Database: {'✅ Initialized' if vector_db.get_collection_stats()['status'] != 'error' else '❌ Error'}")
    except Exception as e:
        print(f"🗄️  Vector Database: ❌ Error - {e}")
    
    # Initialize document store (loads existing documents)
    try:
        from app.document_store import document_store
        print(f"📚 Document Store: ✅ Loaded {document_store.get_document_count()} documents")
    except Exception as e:
        print(f"📚 Document Store: ❌ Error - {e}")
    
    # Run cleanup to ensure data consistency
    try:
        from app.cleanup import cleanup_invalid_registry_entries
        cleanup_invalid_registry_entries()
        print("🧹 Cleanup: ✅ Completed")
    except Exception as e:
        print(f"🧹 Cleanup: ❌ Error - {e}")

if __name__ == "__main__":
    print("🚀 Starting RAG Chatbot Backend Server...")
    print(f"📡 API will be available at: http://localhost:{API_PORT}")
    print(f"🌐 External access: http://YOUR_IP_ADDRESS:{API_PORT}")
    print(f"📚 API Documentation: http://localhost:{API_PORT}/docs")
    print(f"📚 External docs: http://YOUR_IP_ADDRESS:{API_PORT}/docs")
    print(f"🤖 Gemini API: {'✅ Configured' if API_KEY else '❌ Not configured'}")
    print("👥 Development Mode: 🔗 Shared (Team Collaboration)")
    
    uvicorn.run(app, host=API_HOST, port=API_PORT)
