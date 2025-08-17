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
