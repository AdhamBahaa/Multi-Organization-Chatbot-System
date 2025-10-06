"""
Configuration settings for the RAG Chatbot Backend
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
API_KEY = os.getenv("GOOGLE_API_KEY")
API_HOST = "0.0.0.0"
API_PORT = 8002

# CORS Configuration - Allow team access
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3002",
    "http://localhost:3003",
    "http://localhost:3004",
    "http://localhost:3005",
    # Add your friends' IP addresses here
    "http://192.168.1.*:3000",  # Example: Allow all devices in your network
    "http://10.0.0.*:3000",     # Example: Another common network range
]

# File Upload Configuration
ALLOWED_FILE_TYPES = {
    'application/pdf': '.pdf',
    'text/plain': '.txt',
    'application/msword': '.doc',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
    'text/csv': '.csv',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
    'application/vnd.ms-excel': '.xls',
    'text/markdown': '.md'
}

# Explicitly blocked file types (images, executables, etc.)
BLOCKED_FILE_TYPES = {
    # Image files
    'image/jpeg': '.jpg',
    'image/jpg': '.jpg', 
    'image/png': '.png',
    'image/gif': '.gif',
    'image/bmp': '.bmp',
    'image/tiff': '.tiff',
    'image/webp': '.webp',
    'image/svg+xml': '.svg',
    # Video files
    'video/mp4': '.mp4',
    'video/avi': '.avi',
    'video/mov': '.mov',
    'video/wmv': '.wmv',
    # Audio files
    'audio/mpeg': '.mp3',
    'audio/wav': '.wav',
    'audio/ogg': '.ogg',
    # Executable files
    'application/x-executable': '.exe',
    'application/x-msdownload': '.exe',
    'application/x-msi': '.msi'
}

# Development Mode Configuration - Shared Only
DEV_MODE = "shared"  # Always shared mode for team collaboration

# Upload Directory (shared development only)
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'shared_uploads')

# Chunking/Vector configuration
# Use 'docling' to enable Docling-based advanced chunking
CHUNKING_ENGINE = os.getenv("CHUNKING_ENGINE", "docling")  # options: 'docling', 'chroma'
# When False, vector DB (Chroma) remains present but is not used
USE_VECTOR_DB = os.getenv("USE_VECTOR_DB", "false").lower() in ("1", "true", "yes")

# Docling behavior tuning
# Prefer converting already-extracted text into Docling MD instead of re-parsing the PDF (much faster, avoids heavy model downloads)
DOCLING_PREFER_TEXT = os.getenv("DOCLING_PREFER_TEXT", "true").lower() in ("1", "true", "yes")
# Choose chunker: 'hierarchical' (fast, structure-aware) or 'hybrid' (token-aware, slower and may download extra models)
DOCLING_CHUNKER_MODE = os.getenv("DOCLING_CHUNKER_MODE", "hierarchical").lower()

# Graph Database configuration
USE_GRAPH_DB = os.getenv("USE_GRAPH_DB", "false").lower() in ("1", "true", "yes")
GRAPH_DB_URI = os.getenv("GRAPH_DB_URI", "bolt://localhost:7687")
GRAPH_DB_USER = os.getenv("GRAPH_DB_USER", "neo4j")
GRAPH_DB_PASSWORD = os.getenv("GRAPH_DB_PASSWORD", "password")

# Performance tuning
# Limit number of entities linked per chunk to keep graph sparse and reindex fast
MAX_ENTITIES_PER_CHUNK = int(os.getenv("MAX_ENTITIES_PER_CHUNK", "10"))
# Optional: size of batches for bulk operations (not strictly required, but kept for future use)
GRAPH_BATCH_TX_SIZE = int(os.getenv("GRAPH_BATCH_TX_SIZE", "500"))
"""
Control co-occurrence edge creation. These edges can explode combinatorially per chunk.
Disable or limit to keep reindex fast.
"""
ENABLE_ENTITY_COOCCURRENCE = os.getenv("ENABLE_ENTITY_COOCCURRENCE", "true").lower() in ("1", "true", "yes")
MAX_COOCCURRENCE_PER_CHUNK = int(os.getenv("MAX_COOCCURRENCE_PER_CHUNK", "30"))

# Demo Users (for development only)
DEMO_USERS = {
    "admin": {"id": 1, "username": "admin", "password": "admin123", "role": "admin"},
    "user": {"id": 2, "username": "user", "password": "user123", "role": "user"},
    "demo": {"id": 3, "username": "demo", "password": "demo123", "role": "user"}
}
