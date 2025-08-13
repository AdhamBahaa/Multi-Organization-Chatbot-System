"""
Cleanup utilities for the RAG Chatbot Backend
"""
import os
import shutil
from typing import List
from .config import UPLOAD_DIR
from .document_store import document_store
from .vector_db import vector_db

def cleanup_orphaned_files():
    """Remove files that exist on disk but are not in the document registry"""
    print("🧹 Cleaning up orphaned files...")
    
    # Get all files in uploads directory (excluding chroma_db and registry)
    upload_files = []
    for filename in os.listdir(UPLOAD_DIR):
        file_path = os.path.join(UPLOAD_DIR, filename)
        if os.path.isfile(file_path) and filename != "document_registry.json":
            upload_files.append(file_path)
    
    # Get all registered document file paths
    registered_files = set()
    for doc_data in document_store.get_all_documents():
        file_path = doc_data.get('file_path', '')
        if file_path and os.path.exists(file_path):
            registered_files.add(file_path)
    
    # Find orphaned files
    orphaned_files = [f for f in upload_files if f not in registered_files]
    
    if orphaned_files:
        print(f"🗑️  Found {len(orphaned_files)} orphaned files:")
        for file_path in orphaned_files:
            print(f"   - {os.path.basename(file_path)}")
            try:
                os.remove(file_path)
                print(f"   ✅ Removed: {os.path.basename(file_path)}")
            except Exception as e:
                print(f"   ❌ Error removing {os.path.basename(file_path)}: {e}")
    else:
        print("✅ No orphaned files found")

def cleanup_orphaned_chromadb_entries():
    """Remove ChromaDB entries that don't correspond to registered documents"""
    print("🧹 Cleaning up orphaned ChromaDB entries...")
    
    try:
        # Get all document IDs from ChromaDB
        chroma_results = vector_db.collection.get()
        chroma_doc_ids = set()
        
        if chroma_results['metadatas']:
            for metadata in chroma_results['metadatas']:
                doc_id = metadata.get('document_id', '')
                if doc_id:
                    chroma_doc_ids.add(doc_id)
        
        # Get all registered document IDs
        registered_doc_ids = set(document_store.documents.keys())
        
        # Find orphaned ChromaDB entries
        orphaned_doc_ids = chroma_doc_ids - registered_doc_ids
        
        if orphaned_doc_ids:
            print(f"🗑️  Found {len(orphaned_doc_ids)} orphaned ChromaDB documents:")
            for doc_id in orphaned_doc_ids:
                print(f"   - {doc_id}")
                try:
                    vector_db.delete_document(doc_id)
                    print(f"   ✅ Removed from ChromaDB: {doc_id}")
                except Exception as e:
                    print(f"   ❌ Error removing from ChromaDB {doc_id}: {e}")
        else:
            print("✅ No orphaned ChromaDB entries found")
            
    except Exception as e:
        print(f"❌ Error cleaning up ChromaDB entries: {e}")

def cleanup_invalid_registry_entries():
    """Remove registry entries for files that no longer exist"""
    print("🧹 Cleaning up invalid registry entries...")
    
    invalid_entries = []
    for doc_id, doc_data in document_store.documents.items():
        file_path = doc_data.get('file_path', '')
        if file_path and not os.path.exists(file_path):
            invalid_entries.append(doc_id)
    
    if invalid_entries:
        print(f"🗑️  Found {len(invalid_entries)} invalid registry entries:")
        for doc_id in invalid_entries:
            doc_data = document_store.get_document(doc_id)
            filename = doc_data.get('filename', 'Unknown') if doc_data else 'Unknown'
            print(f"   - {filename} (ID: {doc_id})")
            try:
                document_store.remove_document(doc_id)
                # Also remove from ChromaDB
                vector_db.delete_document(doc_id)
                print(f"   ✅ Removed from registry and ChromaDB: {filename}")
            except Exception as e:
                print(f"   ❌ Error removing {filename}: {e}")
    else:
        print("✅ No invalid registry entries found")

def full_cleanup():
    """Perform a full cleanup of the system"""
    print("🚀 Starting full system cleanup...")
    
    cleanup_invalid_registry_entries()
    cleanup_orphaned_files()
    cleanup_orphaned_chromadb_entries()
    
    print("✅ Full cleanup completed!")

if __name__ == "__main__":
    full_cleanup()
