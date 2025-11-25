"""
Docling-based chunker with forceful debugging, using the official Docling pipeline.

Key change: We no longer import a non-existent `default_chunker` from `docling.chunking`.
Instead, we:
- Build a DoclingDocument via DocumentConverter (from a PDF path or an MD string),
- Then chunk it using HybridChunker (token-aware) or HierarchicalChunker (structure-only).
"""
import sys
import os
from typing import List, Tuple, Optional
from .config import DOCLING_PREFER_TEXT, DOCLING_CHUNKER_MODE

# Lazy imports inside functions to avoid import cost during module import


def _simple_sentence_chunk(text: str, max_chunk_size: int = 1000) -> List[str]:
    """A basic sentence-based chunker."""
    print("--- FALLBACK: Using simple_sentence_chunk ---", file=sys.stderr)
    if not text:
        return []
    sentences = text.split('.')
    chunks: List[str] = []
    current_chunk = ""
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        if len(current_chunk) + len(sentence) + 2 > max_chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + ". "
        else:
            current_chunk += sentence + ". "
    if current_chunk:
        chunks.append(current_chunk.strip())
    if not chunks and text:
        chunks.append(text)
    return chunks


def _chunk_docling_document(dl_doc, prefer_hybrid: bool = True) -> Tuple[List[str], str]:
    """Chunk a DoclingDocument using HybridChunker if possible, else HierarchicalChunker.

    Returns: (chunks, used_engine_label)
    """
    try:
        if prefer_hybrid:
            from docling_core.transforms.chunker.hybrid_chunker import HybridChunker  # type: ignore
            chunker = HybridChunker()
            used = "docling-hybrid"
        else:
            raise ImportError("Force hierarchical")
    except Exception:
        from docling_core.transforms.chunker.hierarchical_chunker import (
            HierarchicalChunker,  # type: ignore
        )
        chunker = HierarchicalChunker()
        used = "docling-hierarchical"

    chunks = [c.text.strip() for c in chunker.chunk(dl_doc) if getattr(c, "text", None)]
    chunks = [c for c in chunks if c]
    return chunks, used


def _convert_pdf_to_docling(pdf_path: str):
    from docling.document_converter import DocumentConverter  # type: ignore
    from docling.datamodel.base_models import InputFormat  # type: ignore

    conv = DocumentConverter()
    res = conv.convert(pdf_path)
    return res.document


def _convert_text_to_docling_md(text: str):
    from docling.document_converter import DocumentConverter  # type: ignore
    from docling.datamodel.base_models import InputFormat  # type: ignore

    conv = DocumentConverter()
    res = conv.convert_string(content=text, format=InputFormat.MD, name="inline.md")
    return res.document


def chunk_text_with_docling(pdf_path: str, text: str, max_chunk_size: int = 1000, prefer_hybrid: Optional[bool] = None) -> Tuple[List[str], str]:
    """
    Attempt Docling-based structural chunking from a PDF path.
    This version includes forceful print statements for debugging.
    """
    print("\n--- CHUNKING PROCESS STARTED ---", file=sys.stderr)

    if prefer_hybrid is None:
        prefer_hybrid = DOCLING_CHUNKER_MODE == "hybrid"

    if DOCLING_PREFER_TEXT or not pdf_path:
        print("--- REASON: No PDF path provided. Will attempt Docling via MD conversion. ---", file=sys.stderr)
        try:
            dl_doc = _convert_text_to_docling_md(text)
            chunks, engine = _chunk_docling_document(dl_doc, prefer_hybrid=prefer_hybrid)
            if chunks:
                print(f"--- SUCCESS: Docling(MD) produced {len(chunks)} chunks. ---", file=sys.stderr)
                return chunks, engine
        except Exception as e:
            print(f"--- Docling(MD) failed: {e}. ---", file=sys.stderr)
        return _simple_sentence_chunk(text, max_chunk_size), "simple"

    # Check file existence
    try:
        exists = os.path.exists(pdf_path)
        print(f"--- PDF Path: {pdf_path} exists={exists} ---", file=sys.stderr)
        if not exists:
            # Try alternate resolution to project root shared_uploads using basename
            try:
                basename = os.path.basename(pdf_path)
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                alt_path = os.path.join(project_root, 'shared_uploads', basename)
                alt_exists = os.path.exists(alt_path)
                print(f"--- ALT PDF Path: {alt_path} exists={alt_exists} ---", file=sys.stderr)
                if alt_exists:
                    pdf_path = alt_path
                else:
                    print("--- REASON: Neither original nor alt PDF path exists. Will attempt Docling(text). ---", file=sys.stderr)
                    # Try Docling via MD conversion before fallback
                    try:
                        dl_doc = _convert_text_to_docling_md(text)
                        chunks, engine = _chunk_docling_document(dl_doc, prefer_hybrid=prefer_hybrid)
                        if chunks:
                            print(f"--- SUCCESS: Docling(MD) produced {len(chunks)} chunks. ---", file=sys.stderr)
                            return chunks, engine
                    except Exception as e:
                        print(f"--- Docling(MD) failed: {e}. ---", file=sys.stderr)
                    return _simple_sentence_chunk(text, max_chunk_size), "fallback: simple"
            except Exception as e:
                print(f"--- ERROR resolving alt PDF path: {e}. Will attempt Docling(text). ---", file=sys.stderr)
                try:
                    dl_doc = _convert_text_to_docling_md(text)
                    chunks, engine = _chunk_docling_document(dl_doc, prefer_hybrid=prefer_hybrid)
                    if chunks:
                        print(f"--- SUCCESS: Docling(MD) produced {len(chunks)} chunks. ---", file=sys.stderr)
                        return chunks, engine
                except Exception as e2:
                    print(f"--- Docling(MD) failed: {e2}. ---", file=sys.stderr)
                return _simple_sentence_chunk(text, max_chunk_size), "fallback: simple"
    except Exception as e:
        print(f"--- ERROR checking PDF path: {e}. Fallback. ---", file=sys.stderr)
        return _simple_sentence_chunk(text, max_chunk_size), "fallback: simple"

    try:
        print(f"--- Attempting to convert and chunk '{pdf_path}' with Docling... ---", file=sys.stderr)
        dl_doc = _convert_pdf_to_docling(pdf_path)
        chunks, engine = _chunk_docling_document(dl_doc, prefer_hybrid=prefer_hybrid)
        if not chunks:
            print("--- REASON: Docling returned no chunks. ---", file=sys.stderr)
            raise ValueError("Docling returned no chunks")
        print(f"--- SUCCESS: Chunked with Docling, found {len(chunks)} chunks. ---", file=sys.stderr)
        return chunks, engine

    except Exception as e:
        import traceback
        print("--- FATAL: Docling chunker failed. ---", file=sys.stderr)
        print(f"--- ERROR: {e} ---", file=sys.stderr)
        print("--- TRACEBACK ---", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        print("--- END TRACEBACK ---", file=sys.stderr)
        return _simple_sentence_chunk(text, max_chunk_size), "fallback: simple"


def simple_sentence_chunk(text: str, max_chunk_size: int = 1000) -> List[str]:
    """Public wrapper for the simple sentence-based chunker."""
    return _simple_sentence_chunk(text, max_chunk_size)


def chunk_text_with_docling_debug(pdf_path: str, text: str, max_chunk_size: int = 1000, prefer_hybrid: Optional[bool] = None) -> Tuple[List[str], str]:
    """Debug version that returns chunks and the engine used."""
    return chunk_text_with_docling(pdf_path, text, max_chunk_size, prefer_hybrid=prefer_hybrid)


def chunk_text_with_docling_with_debug_info(pdf_path: str, text: str, max_chunk_size: int = 1000, prefer_hybrid: Optional[bool] = None):
    """Return (chunks, used_engine, debug_info) capturing decision points for troubleshooting."""
    debug = {
        "pdf_path": pdf_path,
        "pdf_exists": None,
        "alt_path": None,
        "alt_exists": None,
        "docling_text_attempted": False,
        "docling_text_error": None,
        "docling_text_chunks": 0,
        "docling_engine": None,
    }

    print("\n--- CHUNKING VERBOSE START ---", file=sys.stderr)
    if prefer_hybrid is None:
        prefer_hybrid = DOCLING_CHUNKER_MODE == "hybrid"
    debug["prefer_hybrid"] = prefer_hybrid
    debug["prefer_text"] = DOCLING_PREFER_TEXT

    if DOCLING_PREFER_TEXT or not pdf_path:
        print("--- VERBOSE: No PDF path provided. ---", file=sys.stderr)
        # Try Docling via MD conversion
        try:
            debug["docling_text_attempted"] = True
            dl_doc = _convert_text_to_docling_md(text)
            chunks, engine = _chunk_docling_document(dl_doc, prefer_hybrid=prefer_hybrid)
            debug["docling_text_chunks"] = len(chunks)
            debug["docling_engine"] = engine
            if chunks:
                print(f"--- VERBOSE: Docling(MD) produced {len(chunks)} chunks. ---", file=sys.stderr)
                return chunks, engine, debug
        except Exception as e:
            debug["docling_text_error"] = str(e)
            print(f"--- VERBOSE: Docling(MD) failed: {e} ---", file=sys.stderr)
        # fallback
        return _simple_sentence_chunk(text, max_chunk_size), "simple", debug

    # With PDF path provided
    try:
        exists = os.path.exists(pdf_path)
        debug["pdf_exists"] = exists
        print(f"--- VERBOSE PDF Path: {pdf_path} exists={exists} ---", file=sys.stderr)
        if not exists:
            basename = os.path.basename(pdf_path)
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            alt_path = os.path.join(project_root, 'shared_uploads', basename)
            debug["alt_path"] = alt_path
            alt_exists = os.path.exists(alt_path)
            debug["alt_exists"] = alt_exists
            print(f"--- VERBOSE ALT Path: {alt_path} exists={alt_exists} ---", file=sys.stderr)
            if alt_exists:
                pdf_path = alt_path
            else:
                # Try Docling via MD conversion
                try:
                    debug["docling_text_attempted"] = True
                    dl_doc = _convert_text_to_docling_md(text)
                    chunks, engine = _chunk_docling_document(dl_doc, prefer_hybrid=prefer_hybrid)
                    debug["docling_text_chunks"] = len(chunks)
                    debug["docling_engine"] = engine
                    if chunks:
                        print(f"--- VERBOSE: Docling(MD) produced {len(chunks)} chunks. ---", file=sys.stderr)
                        return chunks, engine, debug
                except Exception as e:
                    debug["docling_text_error"] = str(e)
                    print(f"--- VERBOSE: Docling(MD) failed: {e} ---", file=sys.stderr)
                return _simple_sentence_chunk(text, max_chunk_size), "fallback: simple", debug
    except Exception as e:
        print(f"--- VERBOSE: Error checking PDF path: {e} ---", file=sys.stderr)
        debug["pdf_exists"] = False
        # Try Docling via MD conversion
        try:
            debug["docling_text_attempted"] = True
            dl_doc = _convert_text_to_docling_md(text)
            chunks, engine = _chunk_docling_document(dl_doc, prefer_hybrid=prefer_hybrid)
            debug["docling_text_chunks"] = len(chunks)
            debug["docling_engine"] = engine
            if chunks:
                return chunks, engine, debug
        except Exception as e2:
            debug["docling_text_error"] = str(e2)
        return _simple_sentence_chunk(text, max_chunk_size), "fallback: simple", debug

    # If we reach here, PDF path exists. Convert and chunk via Docling.
    try:
        dl_doc = _convert_pdf_to_docling(pdf_path)
        chunks, engine = _chunk_docling_document(dl_doc)
        debug["docling_text_chunks"] = len(chunks)
        debug["docling_engine"] = engine
        if chunks:
            return chunks, engine, debug
    except Exception as e:
        debug["docling_text_error"] = str(e)
    return _simple_sentence_chunk(text, max_chunk_size), "fallback: simple", debug


