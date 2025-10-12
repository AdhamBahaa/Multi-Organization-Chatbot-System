"""
Vector Database module using ChromaDB for the RAG Chatbot Backend
"""
from __future__ import annotations

import os
import re
from typing import List, Dict, Optional

from .config import UPLOAD_DIR, USE_VECTOR_DB, CHUNKING_ENGINE, ODDADMIX_CHUNK_SIZE, ODDADMIX_CHUNK_OVERLAP


class VectorDatabase:
    """Wrapper around ChromaDB with English/Arabic support and safe fallbacks."""

    def __init__(self) -> None:
        self.client = None
        self.collection = None
        self.embedding_function = None
        self.chroma_dir = os.path.join(UPLOAD_DIR, "chroma_db")

        if not USE_VECTOR_DB:
            print("ℹ️ Vector DB disabled by config; skipping Chroma initialization")
            return

        os.makedirs(self.chroma_dir, exist_ok=True)

        try:
            # Lazy imports so other parts of the app can run even if Chroma stack is missing
            import chromadb  # type: ignore
            from chromadb.config import Settings  # type: ignore
            from chromadb.utils.embedding_functions import (
                SentenceTransformerEmbeddingFunction,  # type: ignore
            )

            self.client = chromadb.PersistentClient(
                path=self.chroma_dir,
                settings=Settings(anonymized_telemetry=False, allow_reset=True),
            )

            # English + Arabic capable model
            self.embedding_function = SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )

            self.collection = self.client.get_or_create_collection(
                name="documents",
                embedding_function=self.embedding_function,
                metadata={"description": "English & Arabic document embeddings for RAG chatbot"},
            )

            print("✅ Multi-language vector database initialized successfully")
            print("🌍 Using 'all-MiniLM-L6-v2' embedding model (optimized for English & Arabic)")
        except Exception as e:  # pragma: no cover - defensive
            print(
                f"❌ ChromaDB initialization error (continuing without vector DB): {e}"
            )
            self.client = None
            self.collection = None
            self.embedding_function = None

    # ----------------------------- Public API ---------------------------------
    def add_document(self, doc_id: str, text: str, metadata: Dict) -> bool:
        """Add document text and metadata to vector database."""
        if not self.collection:
            print("⚠️ Vector database not available, skipping document addition")
            return False
        try:
            # Prefer Oddadmix if selected, else Docling; fallback to simple
            chunks = []
            used_engine = None
            if CHUNKING_ENGINE == "oddadmix":
                try:
                    from .oddadmix_chunker import chunk_text_with_oddadmix, oddadmix_available
                    if oddadmix_available():
                        chunks, used_engine, odd_debug = chunk_text_with_oddadmix(
                            text,
                            ODDADMIX_CHUNK_SIZE,
                            ODDADMIX_CHUNK_OVERLAP,
                        )
                        impl = odd_debug.get("impl") if isinstance(odd_debug, dict) else None
                        print(f"🧩 Vector index chunking via Oddadmix ({impl or 'unknown impl'}) → {len(chunks)} chunks")
                    else:
                        raise RuntimeError("Oddadmix not available")
                except Exception:
                    pass
            if not chunks:
                try:
                    from .docling_chunker import chunk_text_with_docling
                    chunks, used_engine = chunk_text_with_docling(pdf_path="", text=text, max_chunk_size=1000)
                    print(f"🧩 Vector index chunking via {used_engine} → {len(chunks)} chunks")
                except Exception:
                    chunks = self._split_text_into_chunks(text)
                    used_engine = "simple"
                    print(f"🧩 Vector index chunking via simple fallback → {len(chunks)} chunks")
            for i, chunk in enumerate(chunks):
                chunk_id = f"{doc_id}_chunk_{i}"
                self.collection.add(
                    documents=[chunk],
                    metadatas=[{**metadata, "chunk_index": i, "total_chunks": len(chunks), "chunk_id": chunk_id}],
                    ids=[chunk_id],
                )
            if used_engine:
                print(f"✅ Indexed document {doc_id} using engine '{used_engine}' with {len(chunks)} chunks")
            return True
        except Exception as e:  # pragma: no cover - defensive
            print(f"Error adding document to vector DB: {e}")
            return False

    def search_documents(
        self, query: str, n_results: int = 5, organization_id: Optional[int] = None
    ) -> List[Dict]:
        """Search documents using vector similarity with enhanced Arabic support."""
        if not self.collection:
            print("⚠️ Vector database not available, returning empty search results")
            return []
        try:
            arabic_pattern = r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]"
            is_arabic_query = bool(re.search(arabic_pattern, query))
            if is_arabic_query:
                print(f"🌍 Arabic query detected: '{query}'")
                n_results = max(n_results, 15)

            query_params: Dict = {
                "query_texts": [query],
                "n_results": n_results,
                "include": ["documents", "metadatas", "distances"],
            }
            if organization_id is not None:
                query_params["where"] = {"organization_id": organization_id}
                print(f"🔍 Filtering search to organization {organization_id}")

            print(f"🔍 Executing vector search with {n_results} results...")
            results = self.collection.query(**query_params)

            search_results: List[Dict] = []
            if results.get("documents") and results["documents"][0]:
                print(
                    f"✅ Vector search returned {len(results['documents'][0])} results"
                )
                for i, (doc, metadata, distance) in enumerate(
                    zip(
                        results["documents"][0],
                        results["metadatas"][0],
                        results["distances"][0],
                    )
                ):
                    relevance_score = max(0, 1 - distance)
                    if is_arabic_query and re.search(r"\d+", doc):
                        relevance_score = min(1.0, relevance_score + 0.1)

                    search_results.append(
                        {
                            "document_id": metadata.get("document_id", ""),
                            "filename": metadata.get("filename", ""),
                            "chunk": doc,
                            "chunk_index": metadata.get("chunk_index", 0),
                            "relevance_score": relevance_score,
                            "metadata": metadata,
                        }
                    )
                    print(
                        f"  Result {i+1}: {metadata.get('filename', 'Unknown')} (relevance: {relevance_score:.3f})"
                    )
                    if is_arabic_query and re.search(r"\d+", doc):
                        print("    📊 Contains numbers/statistics - relevance boosted")
            else:
                print("⚠️ Vector search returned no results")
            return search_results
        except Exception as e:  # pragma: no cover - defensive
            print(f"❌ Error in vector search: {e}")
            print("🔄 Falling back to enhanced text search...")
            return []

    def delete_document(self, doc_id: str) -> bool:
        """Delete all chunks for a specific document."""
        if not self.collection:
            print("⚠️ Vector database not available, skipping document deletion")
            return False
        try:
            results = self.collection.get(where={"document_id": doc_id})
            if results.get("ids"):
                self.collection.delete(ids=results["ids"])
            return True
        except Exception as e:  # pragma: no cover - defensive
            print(f"Error deleting document from vector DB: {e}")
            return False

    def get_collection_stats(self) -> Dict:
        """Get statistics about the vector database."""
        if not self.collection:
            return {
                "total_chunks": 0,
                "status": "unavailable",
                "embedding_model": "none",
                "multilingual_support": False,
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
                "embedding_dimensions": embedding_info.get("dimensions", 0),
            }
        except Exception as e:  # pragma: no cover - defensive
            print(f"Error getting vector DB stats: {e}")
            return {
                "total_chunks": 0,
                "status": "error",
                "embedding_model": "error",
                "multilingual_support": False,
            }

    # ---------------------------- Internal helpers ----------------------------
    def _get_embedding_model_info(self) -> Dict:
        """Get information about the current embedding model."""
        try:
            if getattr(self, "embedding_function", None):
                model = self.embedding_function._model
                if hasattr(model, "get_sentence_embedding_dimension"):
                    dimensions = model.get_sentence_embedding_dimension()
                else:
                    dimensions = 384  # Default for all-MiniLM-L6-v2
                return {
                    "model_name": "all-MiniLM-L6-v2",
                    "multilingual": True,
                    "languages": ["English", "Arabic"],
                    "dimensions": dimensions,
                    "description": "Multi-language sentence transformer optimized for English and Arabic",
                }
            return {
                "model_name": "default",
                "multilingual": False,
                "languages": [],
                "dimensions": 0,
                "description": "Default ChromaDB embeddings",
            }
        except Exception as e:  # pragma: no cover - defensive
            print(f"Error getting embedding model info: {e}")
            return {
                "model_name": "unknown",
                "multilingual": False,
                "languages": [],
                "dimensions": 0,
                "description": "Unknown embedding model",
            }

    def _split_text_into_chunks(self, text: str, max_chunk_size: int = 1000) -> List[str]:
        """Split text into chunks for vector storage."""
        sentences = text.split(".")
        chunks: List[str] = []
        current = ""
        for s in sentences:
            s = s.strip()
            if not s:
                continue
            if len(current) + len(s) > max_chunk_size and current:
                chunks.append(current.strip())
                current = s
            else:
                current += s + ". "
        if current.strip():
            chunks.append(current.strip())
        if not chunks:
            chunks = [text[:max_chunk_size]]
        return chunks

    def test_multilingual_embeddings(self) -> Dict:
        """Test English & Arabic embedding capabilities."""
        if not self.collection or not self.embedding_function:
            return {
                "status": "error",
                "message": "Vector database or embedding function not available",
            }
        try:
            test_sentences = [
                "Hello, how are you?",
                "مرحبا، كيف حالك؟",
                "What is the main topic of the documents?",
                "ما هو الموضوع الرئيسي للمستندات؟",
                "Can you explain the key points?",
                "هل يمكنك شرح النقاط الرئيسية؟",
                "Tell me about the content",
                "أخبرني عن المحتوى",
            ]
            embeddings = []
            for sentence in test_sentences:
                embedding = self.embedding_function._model.encode(sentence)
                embeddings.append(
                    {
                        "text": sentence,
                        "embedding_length": len(embedding),
                        "embedding_sample": embedding[:5].tolist(),
                    }
                )
            return {
                "status": "success",
                "message": "English & Arabic embedding test completed",
                "total_sentences": len(test_sentences),
                "embedding_dimensions": embeddings[0]["embedding_length"]
                if embeddings
                else 0,
                "test_results": embeddings,
                "multilingual_support": True,
            }
        except Exception as e:  # pragma: no cover - defensive
            return {
                "status": "error",
                "message": f"Error testing English & Arabic embeddings: {e}",
                "multilingual_support": False,
            }


# Global instance
vector_db = VectorDatabase()


