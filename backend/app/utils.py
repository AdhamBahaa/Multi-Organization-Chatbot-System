"""
Utility functions for the RAG Chatbot Backend
"""
import os
import hashlib
import time
import PyPDF2
import docx
from io import BytesIO
from typing import List, Dict
from .config import UPLOAD_DIR, ALLOWED_FILE_TYPES

# Import the persistent document store
from .document_store import document_store

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
    """Search documents using ChromaDB vector similarity"""
    from .vector_db import vector_db
    
    # Use vector database for semantic search
    vector_results = vector_db.search_documents(query, n_results=5)
    
    # Group results by document
    document_results = {}
    for result in vector_results:
        doc_id = result['document_id']
        if doc_id not in document_results:
            document_results[doc_id] = {
                'document_id': doc_id,
                'filename': result['filename'],
                'chunks': [],
                'relevance': 0
            }
        
        document_results[doc_id]['chunks'].append(result['chunk'])
        document_results[doc_id]['relevance'] += result['relevance_score']
    
    # Convert to list and sort by relevance
    results = list(document_results.values())
    results.sort(key=lambda x: x['relevance'], reverse=True)
    
    return results

def generate_document_id(filename: str) -> str:
    """Generate a unique document ID"""
    return hashlib.md5(f"{filename}{time.time()}".encode()).hexdigest()[:8]

def ensure_upload_directory():
    """Ensure the upload directory exists"""
    os.makedirs(UPLOAD_DIR, exist_ok=True)

def save_file_to_disk(file_content: bytes, doc_id: str, filename: str) -> str:
    """Save uploaded file to disk"""
    ensure_upload_directory()
    file_path = os.path.join(UPLOAD_DIR, f"{doc_id}_{filename}")
    with open(file_path, "wb") as f:
        f.write(file_content)
    return file_path
