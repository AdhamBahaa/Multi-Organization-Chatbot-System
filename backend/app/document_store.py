"""
Persistent Document Store for the RAG Chatbot Backend
"""
import os
import json
import time
from typing import Dict, List, Optional
from .config import UPLOAD_DIR

class DocumentStore:
    def __init__(self):
        """Initialize the persistent document store"""
        self.store_file = os.path.join(UPLOAD_DIR, "document_registry.json")
        self.documents: Dict[str, dict] = {}
        self.load_documents()
    
    def load_documents(self):
        """Load existing documents from the registry file"""
        try:
            if os.path.exists(self.store_file):
                with open(self.store_file, 'r', encoding='utf-8') as f:
                    self.documents = json.load(f)
                
                # Verify that files actually exist
                valid_documents = {}
                for doc_id, doc_data in self.documents.items():
                    if os.path.exists(doc_data.get('file_path', '')):
                        valid_documents[doc_id] = doc_data
                    else:
                        print(f"⚠️  Document file not found, removing from registry: {doc_data.get('filename', 'Unknown')}")
                
                self.documents = valid_documents
                self.save_documents()
                print(f"📚 Loaded {len(self.documents)} documents from registry")
            else:
                print("📚 No existing document registry found")
        except Exception as e:
            print(f"❌ Error loading document registry: {e}")
            self.documents = {}
    
    def save_documents(self):
        """Save current documents to the registry file"""
        try:
            os.makedirs(os.path.dirname(self.store_file), exist_ok=True)
            with open(self.store_file, 'w', encoding='utf-8') as f:
                json.dump(self.documents, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Error saving document registry: {e}")
    
    def add_document(self, doc_id: str, doc_data: dict):
        """Add a document to the store"""
        self.documents[doc_id] = doc_data
        self.save_documents()
    
    def remove_document(self, doc_id: str) -> bool:
        """Remove a document from the store"""
        if doc_id in self.documents:
            del self.documents[doc_id]
            self.save_documents()
            return True
        return False
    
    def get_document(self, doc_id: str) -> Optional[dict]:
        """Get a specific document by ID"""
        return self.documents.get(doc_id)
    
    def get_all_documents(self) -> List[dict]:
        """Get all documents"""
        return list(self.documents.values())
    
    def document_exists(self, doc_id: str) -> bool:
        """Check if a document exists"""
        return doc_id in self.documents
    
    def get_document_count(self) -> int:
        """Get the total number of documents"""
        return len(self.documents)

# Global document store instance
document_store = DocumentStore()
