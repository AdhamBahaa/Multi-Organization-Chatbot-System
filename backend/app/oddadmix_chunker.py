"""
Wrapper around Oddadmix llm-arabic-instruct-gen TextChunker.
Falls back to Docling/simple when the package or its heavy deps are missing.
"""
from __future__ import annotations

from typing import List, Tuple
import os
import sys

# Allow pointing to a local clone if pip install fails
_src_dir = os.getenv("ODDADMIX_SRC_DIR")
if _src_dir and os.path.isdir(_src_dir) and _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)
    # Handle src-layout repositories: if there's a 'src' folder inside, add it too
    _src_src = os.path.join(_src_dir, "src")
    if os.path.isdir(_src_src) and _src_src not in sys.path:
        sys.path.insert(0, _src_src)


def _try_import_text_chunker():
    """Try several plausible import paths for TextChunker and return the class or None."""
    candidates = [
        ("processors", "TextChunker"),  # requires processors/__init__.py to expose TextChunker
        ("processors.chunker", "TextChunker"),  # direct module where class is defined
        ("oddadmix.processors", "TextChunker"),
        ("llm_dataset_instruct_gen.processors", "TextChunker"),
    ]
    for module_name, class_name in candidates:
        try:
            mod = __import__(module_name, fromlist=[class_name])
            cls = getattr(mod, class_name)
            return cls
        except Exception:
            continue
    # fall through to dynamic discovery below
    
    # If a local source directory was provided, try to discover modules dynamically
    _src_dir = os.getenv("ODDADMIX_SRC_DIR")
    if _src_dir and os.path.isdir(_src_dir):
        # Try processors package files inside the provided source dir
        processors_dir = os.path.join(_src_dir, "processors")
        try:
            if os.path.isdir(processors_dir):
                for fname in os.listdir(processors_dir):
                    if not fname.endswith('.py'):
                        continue
                    modname = fname[:-3]
                    full_mod = f"processors.{modname}"
                    try:
                        mod = __import__(full_mod, fromlist=["TextChunker"])  # may raise
                        cls = getattr(mod, "TextChunker", None)
                        if cls:
                            return cls
                    except Exception:
                        # Try importing as a top-level module if package layout differs
                        try:
                            alt_modpath = os.path.join(_src_dir, fname)
                            # Add src dir to sys.path temporarily and import by filename (module name)
                            if _src_dir not in sys.path:
                                sys.path.insert(0, _src_dir)
                            mod = __import__(modname)
                            cls = getattr(mod, "TextChunker", None)
                            if cls:
                                return cls
                        except Exception:
                            continue
        except Exception:
            pass

        # Additionally, try any top-level .py modules in the src dir
        try:
            for fname in os.listdir(_src_dir):
                if not fname.endswith('.py'):
                    continue
                modname = fname[:-3]
                try:
                    if _src_dir not in sys.path:
                        sys.path.insert(0, _src_dir)
                    mod = __import__(modname)
                    cls = getattr(mod, "TextChunker", None)
                    if cls:
                        return cls
                except Exception:
                    continue
        except Exception:
            pass

    return None


def oddadmix_available() -> bool:
    return _try_import_text_chunker() is not None


def chunk_text_with_oddadmix(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> Tuple[List[str], str, dict]:
    """
    Returns: (chunks, used_engine, debug)
    """
    try:
        TextChunker = _try_import_text_chunker()
        if TextChunker is None:
            raise ImportError("Oddadmix TextChunker not found; set ODDADMIX_SRC_DIR or install the package")
        chunker = TextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        chunks = chunker.chunk_text(text)
        # Normalize: ensure list of strings
        chunks = [c for c in (chunks or []) if isinstance(c, str) and c.strip()]
        # Include class/module info for easier diagnostics
        debug = {
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
            "impl": f"{TextChunker.__module__}.{TextChunker.__name__}",
        }
        return chunks, "oddadmix", debug
    except Exception as e:
        return [], "oddadmix-error", {"error": str(e)}
