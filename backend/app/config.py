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

# CORS Configuration
CORS_ORIGINS = ["http://localhost:3000"]

# File Upload Configuration
ALLOWED_FILE_TYPES = {
    'application/pdf': '.pdf',
    'text/plain': '.txt',
    'application/msword': '.doc',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
    'text/csv': '.csv'
}

# Development Mode Configuration - Shared Only
DEV_MODE = "shared"  # Always shared mode for team collaboration

# Upload Directory (shared development only)
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'shared_uploads')

# Demo Users (for development only)
DEMO_USERS = {
    "admin": {"id": 1, "username": "admin", "password": "admin123", "role": "admin"},
    "user": {"id": 2, "username": "user", "password": "user123", "role": "user"},
    "demo": {"id": 3, "username": "demo", "password": "demo123", "role": "user"}
}
