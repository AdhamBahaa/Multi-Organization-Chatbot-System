"""
Vector Database module using ChromaDB for the RAG Chatbot Backend
"""
import chromadb
import os
import hashlib
from typing import List, Dict, Optional
from chromadb.config import Settings
from .config import UPLOAD_DIR

class VectorDatabase:
    def __init__(self):
        """Initialize ChromaDB client and collection"""
        # Create persistent directory for ChromaDB
        self.chroma_dir = os.path.join(UPLOAD_DIR, "chroma_db")
        os.makedirs(self.chroma_dir, exist_ok=True)
        
        try:
            # Initialize ChromaDB client
            self.client = chromadb.PersistentClient(
                path=self.chroma_dir,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name="documents",
                metadata={"description": "Document embeddings for RAG chatbot"}
            )
        except Exception as e:
            print(f"❌ ChromaDB initialization error: {e}")
            print("🔄 Attempting to reset ChromaDB...")
            
            # Try to reset the database
            try:
                import shutil
                if os.path.exists(self.chroma_dir):
                    shutil.rmtree(self.chroma_dir)
                    print("🗑️ Removed old ChromaDB directory")
                
                os.makedirs(self.chroma_dir, exist_ok=True)
                
                # Reinitialize
                self.client = chromadb.PersistentClient(
                    path=self.chroma_dir,
                    settings=Settings(
                        anonymized_telemetry=False,
                        allow_reset=True
                    )
                )
                
                self.collection = self.client.get_or_create_collection(
                    name="documents",
                    metadata={"description": "Document embeddings for RAG chatbot"}
                )
                print("✅ ChromaDB reset and reinitialized successfully")
            except Exception as reset_error:
                print(f"❌ ChromaDB reset failed: {reset_error}")
                # Create a dummy collection for now
                self.collection = None
                self.client = None
    
    def add_document(self, doc_id: str, text: str, metadata: Dict) -> bool:
        """Add document text and metadata to vector database"""
        if not self.collection:
            print("⚠️ Vector database not available, skipping document addition")
            return False
            
        try:
            # Split text into chunks (simple sentence-based chunking)
            chunks = self._split_text_into_chunks(text)
            
            # Generate embeddings and store
            for i, chunk in enumerate(chunks):
                chunk_id = f"{doc_id}_chunk_{i}"
                
                # Add to collection
                self.collection.add(
                    documents=[chunk],
                    metadatas=[{
                        **metadata,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "chunk_id": chunk_id
                    }],
                    ids=[chunk_id]
                )
            
            return True
            
        except Exception as e:
            print(f"Error adding document to vector DB: {e}")
            return False
    
    def search_documents(self, query: str, n_results: int = 5, organization_id: int = None) -> List[Dict]:
        """Search documents using vector similarity"""
        if not self.collection:
            print("⚠️ Vector database not available, returning empty search results")
            return []
            
        try:
            # Build query parameters
            query_params = {
                "query_texts": [query],
                "n_results": n_results,
                "include": ["documents", "metadatas", "distances"]
            }
            
            # Add organization filter if specified
            if organization_id is not None:
                query_params["where"] = {"organization_id": organization_id}
                print(f"🔍 Filtering search to organization {organization_id}")
            
            # Query the collection
            results = self.collection.query(**query_params)
            
            # Process results
            search_results = []
            if results['documents'] and results['documents'][0]:
                for i, (doc, metadata, distance) in enumerate(zip(
                    results['documents'][0],
                    results['metadatas'][0],
                    results['distances'][0]
                )):
                    search_results.append({
                        'document_id': metadata.get('document_id', ''),
                        'filename': metadata.get('filename', ''),
                        'chunk': doc,
                        'chunk_index': metadata.get('chunk_index', 0),
                        'relevance_score': max(0, 1 - distance),  # Convert distance to similarity, ensure non-negative
                        'metadata': metadata
                    })
            
            return search_results
            
        except Exception as e:
            print(f"Error searching vector DB: {e}")
            return []
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete all chunks for a specific document"""
        if not self.collection:
            print("⚠️ Vector database not available, skipping document deletion")
            return False
            
        try:
            # Get all chunks for this document
            results = self.collection.get(
                where={"document_id": doc_id}
            )
            
            if results['ids']:
                # Delete all chunks
                self.collection.delete(ids=results['ids'])
            
            return True
            
        except Exception as e:
            print(f"Error deleting document from vector DB: {e}")
            return False
    
    def get_collection_stats(self) -> Dict:
        """Get statistics about the vector database"""
        if not self.collection:
            return {
                "total_chunks": 0,
                "status": "unavailable"
            }
            
        try:
            count = self.collection.count()
            return {
                "total_chunks": count,
                "status": "operational" if count > 0 else "empty"
            }
        except Exception as e:
            print(f"Error getting vector DB stats: {e}")
            return {
                "total_chunks": 0,
                "status": "error"
            }
    
    def _split_text_into_chunks(self, text: str, max_chunk_size: int = 1000) -> List[str]:
        """Split text into chunks for vector storage"""
        # Simple sentence-based chunking
        sentences = text.split('.')
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # If adding this sentence would make chunk too long, start new chunk
            if len(current_chunk) + len(sentence) > max_chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                current_chunk += sentence + ". "
        
        # Add the last chunk if it has content
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        # Ensure we have at least one chunk
        if not chunks:
            chunks = [text[:max_chunk_size]]
        
        return chunks

# Global vector database instance
vector_db = VectorDatabase()
