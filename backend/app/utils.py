"""
Utility functions for the RAG Chatbot Backend
"""
import os
import hashlib
import time
import PyPDF2
import docx
from io import BytesIO
from typing import List, Dict, Tuple
from .config import (
    UPLOAD_DIR,
    ALLOWED_FILE_TYPES,
    USE_VECTOR_DB,
    USE_GRAPH_DB,
    ENABLE_HYBRID_RETRIEVAL,
    HYBRID_RRF_K,
    HYBRID_MAX_CHUNKS_PER_DOC,
)
import re

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

def search_documents(query: str, organization_id: int = None) -> List[dict]:
    """Search documents. If vector DB is disabled, skip Chroma and use fallback."""
    print(f"🔍 Searching for: '{query}' in organization {organization_id}")

    vector_results: List[dict] = []
    if USE_VECTOR_DB:
        try:
            from .vector_db import vector_db
            vector_results = vector_db.search_documents(query, n_results=10, organization_id=organization_id)
            print(f"📊 Vector search returned {len(vector_results)} results")
        except Exception as e:
            print(f"⚠️ Vector search error, will fallback: {e}")
    else:
        print("ℹ️ Vector DB disabled by config; using enhanced fallback search only")

    # If vector search disabled/failed or returns no results, use enhanced fallback
    if not vector_results:
        return enhanced_fallback_search_documents(query, organization_id)
    
    # Group results by document and retain chunk_ids for graph expansion
    document_results: Dict[str, Dict] = {}
    for result in vector_results:
        doc_id = result['document_id']
        if doc_id not in document_results:
            document_results[doc_id] = {
                'document_id': doc_id,
                'filename': result['filename'],
                'chunks': [],
                'chunk_ids': [],
                'relevance': 0
            }
        
        document_results[doc_id]['chunks'].append(result['chunk'])
        document_results[doc_id]['relevance'] += result['relevance_score']
        # Preserve chunk_id if present in metadata
        meta = result.get('metadata', {})
        cid = meta.get('chunk_id')
        if cid:
            document_results[doc_id]['chunk_ids'].append(cid)
    
    # Convert to list and sort by relevance
    results = list(document_results.values())
    results.sort(key=lambda x: x['relevance'], reverse=True)

    # Optional: fuse with a simple keyword rank using Reciprocal Rank Fusion (RRF)
    if ENABLE_HYBRID_RETRIEVAL:
        # Build a lightweight keyword rank: position by count of keyword hits in doc text
        try:
            # Gather org documents
            if organization_id is not None:
                all_documents = document_store.get_documents_by_organization(organization_id)
            else:
                all_documents = document_store.get_all_documents()
            # Precompute a keyword score per document
            kw_scores: Dict[str, int] = {}
            q_terms = [t for t in re.split(r"\W+", query.lower()) if t]
            for d in all_documents:
                doc_id = d.get("id")
                text = (d.get("extracted_text") or "").lower()
                if not doc_id or not text:
                    continue
                score = 0
                for t in q_terms:
                    if not t:
                        continue
                    # Count occurrences
                    score += text.count(t)
                if score > 0:
                    kw_scores[doc_id] = score
            # Rank documents by keyword score (desc)
            kw_ranked = sorted(kw_scores.items(), key=lambda x: x[1], reverse=True)
            kw_pos = {doc_id: idx for idx, (doc_id, _) in enumerate(kw_ranked)}

            # Build vector rank index for current results
            vec_pos = {r['document_id']: idx for idx, r in enumerate(results)}

            # Apply RRF per document (lower rank index = better)
            def rrf(rank_idx: int, k: int) -> float:
                return 1.0 / (k + rank_idx + 1)

            fused: List[Tuple[dict, float]] = []
            for idx, r in enumerate(results):
                doc_id = r['document_id']
                v = rrf(idx, HYBRID_RRF_K)
                kpos = kw_pos.get(doc_id)
                k = rrf(kpos, HYBRID_RRF_K) if kpos is not None else 0.0
                fused.append((r, v + k))

            fused.sort(key=lambda x: x[1], reverse=True)
            results = [r for r, _ in fused]
        except Exception as e:
            print(f"⚠️ Hybrid retrieval fusion skipped due to error: {e}")
    
    # Optional: Expand with Graph DB context per document
    if USE_GRAPH_DB:
        try:
            from .graph_db import graph_client
            for doc in results:
                chunk_ids = doc.get('chunk_ids', [])
                if not chunk_ids:
                    continue
                expansion = graph_client.expand_related_for_chunks(chunk_ids, max_neighbors=5)
                # Build a concise graph context summary
                entities = set()
                neighbors = []
                for item in expansion:
                    for e in item.get('entities', []) or []:
                        if isinstance(e, str):
                            entities.add(e)
                    for nb in item.get('neighbors', []) or []:
                        name = nb.get('name')
                        relation = nb.get('relation')
                        if name and relation:
                            neighbors.append(f"{relation}: {name}")
                entities_list = sorted(entities)
                graph_context = ""
                if entities_list:
                    graph_context += "Entities mentioned: " + ", ".join(entities_list[:15])
                if neighbors:
                    if graph_context:
                        graph_context += "\n"
                    graph_context += "Related facts: " + "; ".join(neighbors[:15])
                doc['graph_context'] = graph_context
        except Exception as e:
            print(f"⚠️ Graph expansion skipped due to error: {e}")
    
    # Trim excessive chunks per doc to keep prompts tight
    for r in results:
        if isinstance(r.get('chunks'), list) and len(r['chunks']) > HYBRID_MAX_CHUNKS_PER_DOC:
            r['chunks'] = r['chunks'][:HYBRID_MAX_CHUNKS_PER_DOC]

    print(f"📄 Found {len(results)} documents with relevant content")
    return results

def enhanced_fallback_search_documents(query: str, organization_id: int = None) -> List[dict]:
    """Enhanced fallback search with multi-language keyword mapping"""
    print("🔄 Using enhanced fallback search with multi-language support...")
    
    # Get documents from document store (filtered by organization if specified)
    if organization_id is not None:
        all_documents = document_store.get_documents_by_organization(organization_id)
        print(f"📚 Total documents in organization {organization_id}: {len(all_documents)}")
    else:
        all_documents = document_store.get_all_documents()
        print(f"📚 Total documents in store: {len(all_documents)}")
    
    # Multi-language keyword mapping for common terms
    keyword_mapping = {
        # Arabic to English mappings
        'اصابات': ['injury', 'injuries', 'injured'],
        'عدد': ['number', 'count', 'total', 'amount'],
        'كرة القدم': ['football', 'soccer', 'football injury'],
        'مباراة': ['match', 'game', 'tournament'],
        'ساعة': ['hour', 'time', 'duration'],
        'معدل': ['rate', 'incidence', 'frequency'],
        'نوع': ['type', 'category', 'classification'],
        'سبب': ['cause', 'reason', 'factor'],
        'علاج': ['treatment', 'care', 'management'],
        'وقاية': ['prevention', 'protection', 'safety'],
        
        # Specific injury number terms
        'كم': ['how many', 'what is the number', 'count'],
        'الاصابات': ['the injuries', 'injury count', 'injury numbers'],
        'عدد الاصابات': ['number of injuries', 'injury count', 'total injuries'],
        'كم عدد': ['how many', 'what number', 'count of'],
        'العدد': ['the number', 'the count', 'the total'],
        
        # Common injury-related terms
        'كدمة': ['contusion', 'bruise'],
        'التواء': ['sprain', 'twist'],
        'كسر': ['fracture', 'break'],
        'تمزق': ['tear', 'rupture', 'strain'],
        'خلع': ['dislocation'],
        'جرح': ['wound', 'cut', 'laceration'],
        
        # Numbers and statistics
        'مائة': ['hundred', '100'],
        'ألف': ['thousand', '1000'],
        'نصف': ['half', '50%'],
        'ربع': ['quarter', '25%'],
        'ثلث': ['third', '33%'],
        
        # Time-related
        'سنة': ['year', 'annual'],
        'شهر': ['month', 'monthly'],
        'أسبوع': ['week', 'weekly'],
        'يوم': ['day', 'daily']
    }
    
    # Detect if query is in Arabic
    arabic_pattern = r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]'
    is_arabic_query = bool(re.search(arabic_pattern, query))
    
    # Extract keywords from Arabic query and map to English
    search_keywords = []
    if is_arabic_query:
        # Split Arabic query into words and map to English
        arabic_words = query.split()
        
        # Clean and extract meaningful Arabic words
        for word in arabic_words:
            # Remove punctuation and clean the word
            word_clean = re.sub(r'[^\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]', '', word)
            if word_clean and len(word_clean) > 1:  # Only consider words with more than 1 character
                if word_clean in keyword_mapping:
                    search_keywords.extend(keyword_mapping[word_clean])
                    print(f"🌍 Mapped Arabic word '{word_clean}' to English: {keyword_mapping[word_clean]}")
        
        # Also check for common phrases/combinations
        common_phrases = {
            'ما هو عدد': ['what is the number', 'how many', 'count'],
            'كم عدد': ['how many', 'what number', 'count of'],
            'عدد الاصابات': ['number of injuries', 'injury count', 'total injuries'],
            'كم اصابة': ['how many injuries', 'injury count', 'injury numbers']
        }
        
        for phrase, translations in common_phrases.items():
            if phrase in query:
                search_keywords.extend(translations)
                print(f"🌍 Mapped Arabic phrase '{phrase}' to English: {translations}")
        
        # If no specific mappings found, use general injury-related terms
        if not search_keywords:
            search_keywords = ['injury', 'injuries', 'football', 'soccer', 'number', 'count', 'total']
            print(f"🌍 No specific Arabic mappings found, using general terms: {search_keywords}")
        
        # Always include injury-related terms for Arabic queries
        if 'injury' not in search_keywords and 'injuries' not in search_keywords:
            search_keywords.extend(['injury', 'injuries'])
            print(f"🌍 Added injury terms for Arabic query")
    else:
        # For English queries, use the query as is
        search_keywords = [query.lower()]
    
    print(f"🔍 Searching with keywords: {search_keywords}")
    
    results = []
    
    for doc in all_documents:
        # Check if document has extracted text
        if 'extracted_text' in doc and doc['extracted_text']:
            text = doc['extracted_text'].lower()
            print(f"🔍 Searching in: {doc['filename']} ({len(text)} characters)")
            
            # Check if any of the search keywords are in the document
            found_keywords = []
            for keyword in search_keywords:
                if keyword.lower() in text:
                    found_keywords.append(keyword)
            
            if found_keywords:
                print(f"✅ Found keywords in {doc['filename']}: {found_keywords}")
                
                # Split text into chunks and find relevant sentences
                chunks = []
                sentences = text.split('.')
                
                for sentence in sentences:
                    sentence_lower = sentence.lower()
                    # Check if sentence contains any of the found keywords
                    if any(keyword.lower() in sentence_lower for keyword in found_keywords):
                        # Also look for numbers and statistics in the sentence
                        if re.search(r'\d+', sentence):  # Contains numbers
                            chunks.append(sentence.strip())
                        elif any(term in sentence_lower for term in ['injury', 'injuries', 'football', 'soccer']):
                            chunks.append(sentence.strip())
                
                if chunks:
                    # Calculate relevance based on keyword matches
                    relevance = min(0.9, 0.5 + (len(found_keywords) * 0.1))
                    
                    results.append({
                        'document_id': doc['id'],
                        'filename': doc['filename'],
                        'chunks': chunks[:5],  # Limit to 5 chunks
                        'relevance': relevance
                    })
                    print(f"✅ Added {doc['filename']} with {len(chunks)} chunks (relevance: {relevance:.2f})")
            else:
                print(f"❌ No keywords found in: {doc['filename']}")
        else:
            print(f"⚠️ No extracted text in: {doc['filename']}")
    
    print(f"📄 Enhanced fallback search found {len(results)} documents")
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

def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Validate password strength according to strong criteria.
    
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if len(password) > 128:
        return False, "Password must be no more than 128 characters long"
    
    # Check for at least one uppercase letter
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter (A-Z)"
    
    # Check for at least one lowercase letter
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter (a-z)"
    
    # Check for at least one digit
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number (0-9)"
    
    # Check for at least one special character
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    if not any(char in password for char in special_chars):
        return False, "Password must contain at least one special character (!@#$%^&*()_+-=[]{}|;:,.<>&gt;?)"
    
    # Check for common weak patterns
    weak_patterns = [
        'password', '123456', 'qwerty', 'admin', 'user',
        'letmein', 'welcome', 'monkey', 'dragon', 'master'
    ]
    
    password_lower = password.lower()
    for pattern in weak_patterns:
        if pattern in password_lower:
            return False, f"Password cannot contain common weak patterns like '{pattern}'"
    
    # Check for repeated characters (more than 3 in a row)
    if re.search(r'(.)\1{3,}', password):
        return False, "Password cannot contain more than 3 repeated characters in a row"
    

    
    return True, "Password meets all strength requirements"
