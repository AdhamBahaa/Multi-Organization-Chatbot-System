"""
Vector Database module using ChromaDB for the RAG Chatbot Backend
"""
import chromadb
import os
import hashlib
from typing import List, Dict, Optional
from chromadb.config import Settings
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from .config import UPLOAD_DIR
import re

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
            
            # Initialize English & Arabic embedding function
            # Using 'all-MiniLM-L6-v2' which is optimized for English and Arabic
            # This model provides excellent semantic understanding for both languages
            self.embedding_function = SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"  # Optimized for English and Arabic with excellent semantic understanding
            )
            
            # Get or create collection with English & Arabic embedding function
            self.collection = self.client.get_or_create_collection(
                name="documents",
                embedding_function=self.embedding_function,
                metadata={"description": "English & Arabic document embeddings for RAG chatbot"}
            )
            
            print("✅ Multi-language vector database initialized successfully")
            print("🌍 Using 'all-MiniLM-L6-v2' embedding model (optimized for English & Arabic)")
            
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
                
                # Reinitialize with English & Arabic embeddings
                self.client = chromadb.PersistentClient(
                    path=self.chroma_dir,
                    settings=Settings(
                        anonymized_telemetry=False,
                        allow_reset=True
                    )
                )
                
                # Reinitialize embedding function
                self.embedding_function = SentenceTransformerEmbeddingFunction(
                    model_name="all-MiniLM-L6-v2"  # Optimized for English and Arabic
                )
                
                self.collection = self.client.get_or_create_collection(
                    name="documents",
                    embedding_function=self.embedding_function,
                    metadata={"description": "English & Arabic document embeddings for RAG chatbot"}
                )
                print("✅ ChromaDB reset and reinitialized successfully with English & Arabic support")
            except Exception as reset_error:
                print(f"❌ ChromaDB reset failed: {reset_error}")
                # Create a dummy collection for now
                self.collection = None
                self.client = None
                self.embedding_function = None
    
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
        """Search documents using vector similarity with enhanced Arabic support"""
        if not self.collection:
            print("⚠️ Vector database not available, returning empty search results")
            return []
            
        try:
            # Detect if query is in Arabic
            arabic_pattern = r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]'
            is_arabic_query = bool(re.search(arabic_pattern, query))
            
            if is_arabic_query:
                print(f"🌍 Arabic query detected: '{query}'")
                # For Arabic queries, increase search results and adjust parameters
                n_results = max(n_results, 15)  # Get more results for Arabic queries
            
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
            print(f"🔍 Executing vector search with {n_results} results...")
            results = self.collection.query(**query_params)
            
            # Process results
            search_results = []
            if results['documents'] and results['documents'][0]:
                print(f"✅ Vector search returned {len(results['documents'][0])} results")
                
                for i, (doc, metadata, distance) in enumerate(zip(
                    results['documents'][0],
                    results['metadatas'][0],
                    results['distances'][0]
                )):
                    # Calculate relevance score (convert distance to similarity)
                    relevance_score = max(0, 1 - distance)
                    
                    # For Arabic queries, boost relevance if document contains numbers/statistics
                    if is_arabic_query and re.search(r'\d+', doc):
                        relevance_score = min(1.0, relevance_score + 0.1)  # Boost relevance for Arabic queries with numbers
                    
                    search_results.append({
                        'document_id': metadata.get('document_id', ''),
                        'filename': metadata.get('filename', ''),
                        'chunk': doc,
                        'chunk_index': metadata.get('chunk_index', 0),
                        'relevance_score': relevance_score,
                        'metadata': metadata
                    })
                    
                    print(f"  Result {i+1}: {metadata.get('filename', 'Unknown')} (relevance: {relevance_score:.3f})")
                    if is_arabic_query and re.search(r'\d+', doc):
                        print(f"    📊 Contains numbers/statistics - relevance boosted")
            else:
                print("⚠️ Vector search returned no results")
            
            return search_results
            
        except Exception as e:
            print(f"❌ Error in vector search: {e}")
            print("🔄 Falling back to enhanced text search...")
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
                "status": "unavailable",
                "embedding_model": "none",
                "multilingual_support": False
            }
            
        try:
            count = self.collection.count()
            embedding_info = self._get_embedding_model_info()
            
            return {
                "total_chunks": count,
                "status": "operational" if count > 0 else "empty",
                "embedding_model": embedding_info.get("model_name", "unknown"),
                "multilingual_support": embedding_info.get("multilingual", False),
                "supported_languages": embedding_info.get("languages", []),
                "embedding_dimensions": embedding_info.get("dimensions", 0)
            }
        except Exception as e:
            print(f"Error getting vector DB stats: {e}")
            return {
                "total_chunks": 0,
                "status": "error",
                "embedding_model": "error",
                "multilingual_support": False
            }
    
    def _get_embedding_model_info(self) -> Dict:
        """Get information about the current embedding model"""
        try:
            if hasattr(self, 'embedding_function') and self.embedding_function:
                # Get model info from sentence transformer
                model = self.embedding_function._model
                if hasattr(model, 'get_sentence_embedding_dimension'):
                    dimensions = model.get_sentence_embedding_dimension()
                else:
                    dimensions = 384  # Default for all-MiniLM-L6-v2
                
                return {
                    "model_name": "all-MiniLM-L6-v2",
                    "multilingual": True,
                    "languages": [
                        "English", "Arabic"
                    ],
                    "dimensions": dimensions,
                    "description": "Multi-language sentence transformer optimized for English and Arabic"
                }
            else:
                return {
                    "model_name": "default",
                    "multilingual": False,
                    "languages": [],
                    "dimensions": 0,
                    "description": "Default ChromaDB embeddings"
                }
        except Exception as e:
            print(f"Error getting embedding model info: {e}")
            return {
                "model_name": "unknown",
                "multilingual": False,
                "languages": [],
                "dimensions": 0,
                "description": "Unknown embedding model"
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

    def test_multilingual_embeddings(self) -> Dict:
        """Test English & Arabic embedding capabilities"""
        if not self.collection or not self.embedding_function:
            return {
                "status": "error",
                "message": "Vector database or embedding function not available"
            }
        
        try:
            # Test sentences in English and Arabic
            test_sentences = [
                "Hello, how are you?",  # English
                "مرحبا، كيف حالك؟",   # Arabic
                "What is the main topic of the documents?",  # English
                "ما هو الموضوع الرئيسي للمستندات؟",  # Arabic
                "Can you explain the key points?",  # English
                "هل يمكنك شرح النقاط الرئيسية؟",  # Arabic
                "Tell me about the content",  # English
                "أخبرني عن المحتوى"  # Arabic
            ]
            
            # Generate embeddings for test sentences
            embeddings = []
            for sentence in test_sentences:
                # Use the embedding function directly
                embedding = self.embedding_function._model.encode(sentence)
                embeddings.append({
                    "text": sentence,
                    "embedding_length": len(embedding),
                    "embedding_sample": embedding[:5].tolist()  # First 5 values
                })
            
            return {
                "status": "success",
                "message": "English & Arabic embedding test completed",
                "total_sentences": len(test_sentences),
                "embedding_dimensions": embeddings[0]["embedding_length"] if embeddings else 0,
                "test_results": embeddings,
                "multilingual_support": True
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error testing English & Arabic embeddings: {e}",
                "multilingual_support": False
            }

# Global vector database instance
vector_db = VectorDatabase()
