"""
Quick checker for Oddadmix availability. Run from the backend folder:

cd "C:/Users/Adham/Desktop/Chatbot Web/backend"
python scripts/check_oddadmix.py

This prints whether Oddadmix can be imported and the resolved implementation class.
"""
from __future__ import annotations
import sys
import os

# Ensure project root is on sys.path (backend folder)
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from dotenv import load_dotenv

# Load environment variables from the repository .env (if present)
env_path = os.path.join(ROOT, '..', '.env')
if not os.path.exists(env_path):
    # try ROOT/.env
    env_path = os.path.join(ROOT, '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)

try:
    from app.oddadmix_chunker import oddadmix_available, _try_import_text_chunker
    avail = oddadmix_available()
    print(f"oddadmix_available: {avail}")
    cls = _try_import_text_chunker()
    if cls:
        print("impl:", getattr(cls, "__module__", None), getattr(cls, "__name__", None))
    else:
        print("impl: None (TextChunker not found)")
except Exception as e:
    print("Error checking Oddadmix availability:", e)
    raise
