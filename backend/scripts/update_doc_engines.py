"""
Maintenance script: re-chunk documents in the registry and update their
`chunk_count` and `used_engine` fields. Run from the project `backend` folder:

python scripts/update_doc_engines.py

This script is careful and only updates the registry file. It will try Oddadmix first
(if available), then Docling, then the simple fallback. It prints a summary.
"""
from __future__ import annotations
import json
import os
import sys
from pprint import pprint

ROOT = os.path.dirname(os.path.dirname(__file__))
REGISTRY = os.path.join(ROOT, "shared_uploads", "document_registry.json")

# Add project root to path so we can import app modules
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.docling_chunker import simple_sentence_chunk, chunk_text_with_docling_with_debug_info
from app.document_store import document_store
from app.config import ODDADMIX_CHUNK_SIZE, ODDADMIX_CHUNK_OVERLAP

try:
    from app.oddadmix_chunker import chunk_text_with_oddadmix, oddadmix_available
    ODD_AVAILABLE = oddadmix_available()
except Exception:
    ODD_AVAILABLE = False


def rechunk_document(doc_id: str, doc_data: dict):
    text = doc_data.get("extracted_text", "") or ""
    if not text:
        print(f"{doc_id}: no extracted text, skipping")
        return None

    # Try oddadmix first if configured
    chunks = []
    used_engine = None

    if ODD_AVAILABLE:
        try:
            odd_chunks, odd_used, odd_debug = chunk_text_with_oddadmix(text, ODDADMIX_CHUNK_SIZE, ODDADMIX_CHUNK_OVERLAP)
            if odd_chunks:
                chunks = odd_chunks
                used_engine = odd_used
                print(f"{doc_id}: oddadmix produced {len(chunks)} chunks")
        except Exception as e:
            print(f"{doc_id}: oddadmix error: {e}")

    if not chunks:
        # Try docling
        try:
            pdf_path = doc_data.get("file_path", "")
            docling_chunks, docling_engine, docling_debug = chunk_text_with_docling_with_debug_info(pdf_path=pdf_path, text=text, max_chunk_size=1000, prefer_hybrid=True)
            if docling_chunks:
                chunks = docling_chunks
                used_engine = docling_engine
                print(f"{doc_id}: docling ({docling_engine}) produced {len(chunks)} chunks")
        except Exception as e:
            print(f"{doc_id}: docling error: {e}")

    if not chunks:
        chunks = simple_sentence_chunk(text, max_chunk_size=1000)
        used_engine = "simple"
        print(f"{doc_id}: simple fallback produced {len(chunks)} chunks")

    # Update doc_data
    doc_data["chunk_count"] = len(chunks)
    doc_data["used_engine"] = used_engine

    # Persist
    document_store.add_document(doc_id, doc_data)

    return {"id": doc_id, "chunk_count": len(chunks), "used_engine": used_engine}


def main():
    docs = document_store.get_all_documents()
    print(f"Found {len(docs)} documents in registry")
    results = []
    for d in docs:
        doc_id = d.get("id")
        print("-" * 40)
        print(f"Processing {doc_id} - {d.get('filename')}")
        res = rechunk_document(doc_id, d)
        if res:
            results.append(res)

    print("\nSummary:\n")
    pprint(results)


if __name__ == "__main__":
    main()
