"""
Chat functionality module for the RAG Chatbot Backend
"""
import google.generativeai as genai
from .models import ChatRequest, ChatResponse
from .utils import search_documents
from .config import API_KEY, DEBUG_VERBOSITY
from .database import ChatSession, ChatMessage
import re
import time
import hashlib

def configure_gemini():
    """Configure Gemini API if key is available"""
    if API_KEY:
        genai.configure(api_key=API_KEY)

def generate_message_id(session_id: int, user_message: str, timestamp: float) -> int:
    """Generate a unique message ID for feedback tracking"""
    # Create a hash from session_id, user_message, and timestamp
    hash_input = f"{session_id}_{user_message}_{timestamp}"
    hash_object = hashlib.md5(hash_input.encode())
    # Convert first 6 characters of hex digest to integer (to fit in SQL Server int)
    # This gives us a range of 0 to 16,777,215 which fits comfortably in SQL Server int
    return int(hash_object.hexdigest()[:6], 16)

def detect_language(text: str) -> str:
    """Detect the language of the input text - English or Arabic only"""
    # Arabic pattern (Unicode ranges for Arabic script)
    arabic_pattern = r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]'
    
    # Check for Arabic characters first
    if re.search(arabic_pattern, text):
        return "Arabic"
    
    # Check for common Arabic words/phrases
    arabic_words = ['مرحبا', 'كيف', 'حال', 'شكرا', 'نعم', 'لا', 'أهلا', 'سلام', 'ما', 'هو', 'الموضوع', 'الرئيسي', 'للمستندات', 'المرفوعة']
    
    if any(word in text for word in arabic_words):
        return "Arabic"
    
    # Default to English for everything else
    return "English"

def create_multilingual_prompt(user_question: str, document_context: str, detected_language: str) -> str:
    """Create a language-specific prompt for English or Arabic responses"""
    
    # Language-specific instructions for English and Arabic only
    language_instructions = {
        "Arabic": {
            "system": "أنت مساعد ذكي للدردشة يعمل بنظام RAG. أجب على أسئلة المستخدم بناءً على السياق المقدم من المستندات المرفوعة.",
            "rules": [
                "أجب باللغة العربية دائماً",
                "استخدم المعلومات من المستندات المرفوعة عند الإجابة",
                "كن محدداً واذكر المستند الذي جاءت منه المعلومات",
                "إذا لم تجد معلومات ذات صلة، قدم إجابة مفيدة عامة باللغة العربية",
                "استخدم تعبيرات عربية طبيعية ومناسبة للسياق الثقافي"
            ]
        },
        "English": {
            "system": "You are an intelligent RAG chatbot assistant. Answer the user's question based on the provided context from their uploaded documents.",
            "rules": [
                "Always respond in English",
                "Use information from uploaded documents when answering",
                "Be specific and mention which document the information came from",
                "If you cannot find relevant information, provide a general helpful response in English",
                "Use natural English expressions and appropriate cultural context"
            ]
        }
    }
    
    # Get language-specific instructions
    lang_instructions = language_instructions.get(detected_language, language_instructions["English"])
    
    # Create the prompt
    prompt = f"""{lang_instructions['system']}

CORE RULE: You MUST respond in {detected_language} language.

User Question ({detected_language}): {user_question}

{document_context}

Instructions:
{chr(10).join(f"- {rule}" for rule in lang_instructions['rules'])}

Additional Requirements:
- Maintain the same language throughout your response
- If the document context contains relevant information, use it to answer the question
- If no relevant information is found in the documents, provide a general helpful response
- Be specific and reference the information from the documents when applicable
- If you mention information from documents, indicate which document it came from
- Ensure your response is natural and fluent in {detected_language}
- Use appropriate cultural context and expressions for {detected_language} speakers
- **CRITICAL: Use plain text formatting only - NO Markdown, NO asterisks (*), NO bold (**), NO special formatting**
- **IMPORTANT: Present information in clear, readable paragraphs without bullet points or special symbols**
- **FORMATTING RULE: Use simple text with line breaks and clear structure, but avoid any Markdown syntax**

Remember: Your response must be entirely in {detected_language} language and use plain text formatting only."""
    
    return prompt

async def generate_chat_response(chat_data: ChatRequest, organization_id: int = None) -> ChatResponse:
    """Generate AI-powered response with RAG functionality and English/Arabic language support"""
    
    if DEBUG_VERBOSITY >= 1:
        print(f"🤖 Generating response for: '{chat_data.message}' in organization {organization_id}")
    
    # Detect the language of the user's question (English or Arabic)
    detected_language = detect_language(chat_data.message)
    if DEBUG_VERBOSITY >= 1:
        print(f"🌍 Detected language: {detected_language}")
    
    # Search through uploaded documents (filtered by organization)
    # The vector database now supports English and Arabic document search
    search_results = search_documents(chat_data.message, organization_id)
    if DEBUG_VERBOSITY >= 1:
        print(f"📋 Search returned {len(search_results)} document results")
    
    # Debug: Print search results for troubleshooting
    if DEBUG_VERBOSITY >= 2:
        for i, result in enumerate(search_results):
            print(f"  Result {i+1}: {result['filename']} (relevance: {result['relevance']:.3f})")
            print(f"    Chunks: {len(result['chunks'])}")
            if result['chunks']:
                print(f"    Sample chunk: {result['chunks'][0][:100]}...")
    
    # Prepare context from documents (vector chunks + optional graph expansion)
    document_context = ""
    sources = []
    # Live retrieval debug container
    debug_info = {
        "docs_considered": len(search_results),
        "documents": [],
        "all_chunk_ids": [],
        "total_chunks_used": 0,
    }
    # Heuristic: if results have chunk_ids, vector retrieval was used; otherwise fallback
    try:
        has_chunk_ids = any(isinstance(r.get('chunk_ids'), list) and r['chunk_ids'] for r in search_results)
        debug_info["retrieval_mode"] = "vector" if has_chunk_ids else "fallback"
    except Exception:
        debug_info["retrieval_mode"] = "unknown"
    
    if search_results:
        document_context = f"\n\nRelevant information from uploaded documents:\n"
        
        # Filter sources based on relevance threshold
        relevant_sources = []
        for result in search_results[:5]:  # Use top 5 most relevant documents
            # Include sources with reasonable relevance (above 0.2 threshold)
            if result['relevance'] > 0.2:
                document_context += f"\nFrom {result['filename']}:\n"
                for chunk in result['chunks']:
                    if chunk.strip():
                        document_context += f"- {chunk.strip()}\n"
                # Attach optional graph context if present
                graph_ctx = result.get('graph_context')
                if graph_ctx:
                    document_context += f"(Graph context) {graph_ctx}\n"
                
                relevant_sources.append({
                    "document_id": result['document_id'],
                    "filename": result['filename'],
                    "relevance": result['relevance']
                })
                # Collect per-document debug info
                doc_chunk_ids = result.get('chunk_ids', []) or []
                vector_chunk_ids = result.get('vector_chunk_ids', []) or []
                vector_chunks = result.get('vector_chunks', []) or []
                vector_titles = result.get('vector_chunk_titles', []) or []
                graph_entities = result.get('graph_entities', []) or []
                graph_neighbors = result.get('graph_neighbors', []) or []
                doc_debug_entry = {
                    "document_id": result.get("document_id"),
                    "filename": result.get("filename"),
                    "relevance": result.get("relevance"),
                    "num_chunks": len(result.get("chunks", [])),
                    "chunk_ids": doc_chunk_ids,
                    # Parallel list of human-friendly titles for the vector chunks (best effort)
                    "chunk_titles": result.get("vector_chunk_titles", []) or [],
                    # The exact text chunks included in the prompt context
                    "chunks": result.get("chunks", []),
                    "vector": {
                        "chunk_ids": vector_chunk_ids,
                        "chunks": vector_chunks,
                        "titles": vector_titles,
                    },
                    "graph": {
                        "entities": graph_entities,
                        "neighbors": graph_neighbors,
                        "context": result.get("graph_context", ""),
                    }
                }
                debug_info["documents"].append(doc_debug_entry)
                debug_info["all_chunk_ids"].extend(doc_chunk_ids)
                debug_info["total_chunks_used"] += len(result.get("chunks", []))

                # Optional verbose preview in logs
                if DEBUG_VERBOSITY >= 2:
                    try:
                        used_chunks = result.get("chunks", [])
                        print(f"🧩 Chunks chosen from {result.get('filename')}: {len(used_chunks)}")
                        for idx, ch in enumerate(used_chunks[:3]):
                            cid = (vector_chunk_ids[idx] if idx < len(vector_chunk_ids) else 'n/a')
                            title = (vector_titles[idx] if idx < len(vector_titles) and vector_titles[idx] else 'chunk')
                            preview = ch.strip().replace('\n', ' ')[:120]
                            # Show human-friendly title first, keep id for traceability
                            print(f"   • [{idx}] {title} (id={cid}) → {preview}{'…' if len(ch) > 120 else ''}")
                    except Exception:
                        pass
        
        sources = relevant_sources  # Only include highly relevant sources
        if DEBUG_VERBOSITY >= 1:
            names = ", ".join(s.get("filename", "?") for s in sources)
            # Build a concise retrieval summary from debug_info
            try:
                vec_chunks = sum(len(d.get("vector", {}).get("chunk_ids", []) or []) for d in debug_info.get("documents", []))
                graph_entities = sum(len(d.get("graph", {}).get("entities", []) or []) for d in debug_info.get("documents", []))
                graph_neighbors = sum(len(d.get("graph", {}).get("neighbors", []) or []) for d in debug_info.get("documents", []))
                mode = debug_info.get("retrieval_mode", "unknown")
                print(f"📄 Using context from {len(sources)} docs: {names}")
                print(f"🧭 Retrieval summary → mode={mode}, vectorChunks={vec_chunks}, graphEntities={graph_entities}, graphNeighbors={graph_neighbors}")
            except Exception:
                print(f"📄 Using context from {len(sources)} docs: {names}")
    else:
        if DEBUG_VERBOSITY >= 1:
            print("⚠️ No relevant documents found")
        document_context = f"\n\nNo relevant information found in uploaded documents."
    
    # Generate response using Gemini with enhanced English/Arabic language prompt
    try:
        if API_KEY:
            model = genai.GenerativeModel("gemini-2.0-flash")
            
            # Create English or Arabic language-specific prompt
            prompt = create_multilingual_prompt(chat_data.message, document_context, detected_language)
            
            response = model.generate_content(
                prompt,
                                    generation_config=genai.types.GenerationConfig(
                        temperature=0.1,  # Lower temperature for more consistent, accurate responses
                        max_output_tokens=1000,  # Increased for more detailed English/Arabic responses
                        top_p=0.8,  # Add top_p for better response quality
                        top_k=40,   # Add top_k for better response quality
                    )
            )
            ai_response = response.text.strip()
            
            # Debug: Print the raw AI response before cleanup
            if DEBUG_VERBOSITY >= 2:
                print(f"🔍 Raw AI response: {repr(ai_response)}")
            # Clean up any remaining Markdown formatting to ensure plain text
            # This removes asterisks, bold formatting, and converts any remaining Markdown to clean text
            # Remove Markdown formatting (Unicode-aware)
            ai_response = re.sub(r'\*\*([^*]+)\*\*', r'\1', ai_response, flags=re.UNICODE)  # Remove **bold**
            ai_response = re.sub(r'\*([^*]+)\*', r'\1', ai_response, flags=re.UNICODE)       # Remove *italic*
            ai_response = re.sub(r'^\s*\*\s*', '- ', ai_response, flags=re.UNICODE)          # Convert leading * to -
            ai_response = re.sub(r'\n\s*\*\s*', '\n- ', ai_response, flags=re.UNICODE)       # Convert * to - in middle
            ai_response = re.sub(r'^\s*-\s*', '', ai_response, flags=re.UNICODE)             # Remove leading -
            ai_response = re.sub(r'\n\s*-\s*', '\n', ai_response, flags=re.UNICODE)          # Remove - in middle
            # Clean up extra whitespace
            ai_response = re.sub(r'\n\s*\n\s*\n', '\n\n', ai_response, flags=re.UNICODE)     # Remove excessive line breaks
            ai_response = ai_response.strip()
            
            # Debug: Print the cleaned AI response
            if DEBUG_VERBOSITY >= 2:
                print(f"🔍 Cleaned AI response: {repr(ai_response)}")

            # LangChain-based validation and correction
            try:
                from .validation import validate_and_fix_response
                # Provide the document_context to enable fact-checking
                print(f"[chat] Passing context to validator: {len(document_context)} chars")
                ai_response = validate_and_fix_response(chat_data.message, ai_response, detected_language, context_text=document_context)
            except Exception as _:
                pass
            
            # Verify the response is in the correct language
            response_language = detect_language(ai_response)
            if response_language != detected_language and detected_language != "English":
                print(f"⚠️ Language mismatch: Expected {detected_language}, got {response_language}")
                # Regenerate with stronger Arabic language enforcement
                stronger_prompt = prompt + f"\n\nCRITICAL: You MUST respond ONLY in {detected_language}. Do not use any other language."
                response = model.generate_content(
                    stronger_prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.05,  # Even lower temperature for strict Arabic language adherence
                        max_output_tokens=1000,
                        top_p=0.7,
                        top_k=30,
                    )
                )
                ai_response = response.text.strip()
                
                # Clean up any remaining Markdown formatting for fallback response too
                # This ensures consistent plain text formatting across all responses
                ai_response = re.sub(r'\*\*([^*]+)\*\*', r'\1', ai_response, flags=re.UNICODE)  # Remove **bold**
                ai_response = re.sub(r'\*([^*]+)\*', r'\1', ai_response, flags=re.UNICODE)       # Remove *italic*
                ai_response = re.sub(r'^\s*\*\s*', '- ', ai_response, flags=re.UNICODE)          # Convert leading * to -
                ai_response = re.sub(r'\n\s*\*\s*', '\n- ', ai_response, flags=re.UNICODE)       # Convert * to - in middle
                ai_response = re.sub(r'^\s*-\s*', '', ai_response, flags=re.UNICODE)             # Remove leading -
                ai_response = re.sub(r'\n\s*-\s*', '\n', ai_response, flags=re.UNICODE)          # Remove - in middle
                # Clean up extra whitespace
                ai_response = re.sub(r'\n\s*\n\s*\n', '\n\n', ai_response, flags=re.UNICODE)     # Remove excessive line breaks
                ai_response = ai_response.strip()
                # Validate again after regeneration
                try:
                    from .validation import validate_and_fix_response
                    print(f"[chat] Re-validation with context after regeneration: {len(document_context)} chars")
                    ai_response = validate_and_fix_response(chat_data.message, ai_response, detected_language, context_text=document_context)
                except Exception:
                    pass
            
        else:
            ai_response = f"I'm a demo RAG chatbot. The Gemini API is not configured, so this is a mock response. Please configure the GOOGLE_API_KEY environment variable to enable AI responses."
    
    except Exception as e:
        ai_response = f"AI service temporarily unavailable: {str(e)}"
    
    # Mock session ID if not provided
    session_id = chat_data.session_id or 1
    
    # Generate unique message ID for feedback tracking
    timestamp = time.time()
    message_id = generate_message_id(session_id, chat_data.message, timestamp)
    
    # Calculate dynamic confidence based on relevance scores
    if search_results:
        # Calculate average relevance score from all sources
        total_relevance = sum(result['relevance'] for result in search_results)
        avg_relevance = total_relevance / len(search_results)
        
        # Convert relevance score to confidence (0.0 to 1.0)
        # Relevance scores are typically between 0.0 and 1.0, where higher is better
        confidence = min(avg_relevance, 1.0)  # Cap at 1.0
        
        # Ensure minimum confidence of 0.3 for found results
        confidence = max(confidence, 0.3)
    else:
        confidence = 0.1  # Very low confidence when no documents found
    
    return ChatResponse(
        response=ai_response,
        session_id=session_id,
        message_id=message_id,
        sources=sources,
        confidence=confidence,
        chunks_found=debug_info.get("total_chunks_used", len(search_results)),
        debug=debug_info
    )

async def get_user_sessions():
    """Get user's chat sessions (mock response)"""
    return [
        {
            "id": 1,
            "title": "Demo Chat Session",
            "created_at": "2025-08-10T00:00:00",
            "message_count": 5
        }
    ]
