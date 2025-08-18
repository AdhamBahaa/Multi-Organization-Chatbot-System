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
        print(f"📄 Extracting text from {filename} ({content_type})")
        
        if content_type == 'text/plain':
            text = file_content.decode('utf-8', errors='ignore')
            print(f"✅ Text file extracted: {len(text)} characters")
            return text
        
        elif content_type == 'application/pdf':
            try:
                # Try PyPDF2 first
                pdf_file = BytesIO(file_content)
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                text = ""
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                        print(f"📄 PDF page {page_num + 1}: {len(page_text)} characters")
                
                if text.strip():
                    print(f"✅ PDF extracted: {len(text)} total characters")
                    return text
                else:
                    print("⚠️ PDF extraction returned empty text")
                    return f"PDF file uploaded: {filename}. Content extraction returned empty text, but file is stored."
                    
            except Exception as e:
                print(f"❌ PDF extraction error: {e}")
                return f"PDF file uploaded: {filename}. Content extraction failed: {str(e)}"
        
        elif content_type in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/msword']:
            try:
                doc_file = BytesIO(file_content)
                doc = docx.Document(doc_file)
                text = ""
                for paragraph in doc.paragraphs:
                    if paragraph.text.strip():
                        text += paragraph.text + "\n"
                
                if text.strip():
                    print(f"✅ DOCX extracted: {len(text)} characters")
                    return text
                else:
                    print("⚠️ DOCX extraction returned empty text")
                    return f"Word document uploaded: {filename}. Content extraction returned empty text, but file is stored."
                    
            except Exception as e:
                print(f"❌ DOCX extraction error: {e}")
                return f"Word document uploaded: {filename}. Content extraction failed: {str(e)}"
        
        elif content_type == 'text/csv':
            text = file_content.decode('utf-8', errors='ignore')
            print(f"✅ CSV extracted: {len(text)} characters")
            return text
        
        else:
            print(f"⚠️ Unsupported file type: {content_type}")
            return f"File uploaded: {filename}. Text extraction not supported for {content_type}."
    
    except Exception as e:
        print(f"❌ Text extraction error: {e}")
        return f"File uploaded: {filename}. Content extraction failed: {str(e)}"

def search_documents(query: str) -> List[dict]:
    """Search documents using ChromaDB vector similarity with fallback"""
    from .vector_db import vector_db
    
    print(f"🔍 Searching for: '{query}'")
    
    # Use vector database for semantic search
    vector_results = vector_db.search_documents(query, n_results=5)
    print(f"📊 Vector search returned {len(vector_results)} results")
    
    # If vector search fails or returns no results, try fallback search
    if not vector_results:
        print("⚠️ Vector search failed, trying fallback search...")
        return fallback_search_documents(query)
    
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
    
    print(f"📄 Found {len(results)} documents with relevant content")
    return results

def fallback_search_documents(query: str) -> List[dict]:
    """Fallback search using simple text matching"""
    print("🔄 Using fallback search...")
    
    # Get all documents from document store
    all_documents = document_store.get_all_documents()
    print(f"📚 Total documents in store: {len(all_documents)}")
    
    results = []
    query_lower = query.lower()
    
    for doc in all_documents:
        # Check if document has extracted text
        if 'extracted_text' in doc and doc['extracted_text']:
            text = doc['extracted_text'].lower()
            print(f"🔍 Searching in: {doc['filename']} ({len(text)} characters)")
            
            # Simple keyword matching
            if query_lower in text:
                # Split text into chunks around the query
                chunks = []
                sentences = text.split('.')
                for sentence in sentences:
                    if query_lower in sentence.lower():
                        chunks.append(sentence.strip())
                
                if chunks:
                    results.append({
                        'document_id': doc['id'],
                        'filename': doc['filename'],
                        'chunks': chunks[:3],  # Limit to 3 chunks
                        'relevance': 0.7  # Default relevance for fallback
                    })
                    print(f"✅ Found match in: {doc['filename']} ({len(chunks)} chunks)")
            else:
                print(f"❌ No match found in: {doc['filename']}")
        else:
            print(f"⚠️ No extracted text in: {doc['filename']}")
    
    print(f"📄 Fallback search found {len(results)} documents")
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
