"""
Chat functionality module for the RAG Chatbot Backend
"""
import google.generativeai as genai
from .models import ChatRequest, ChatResponse
from .utils import search_documents
from .config import API_KEY
import re

def configure_gemini():
    """Configure Gemini API if key is available"""
    if API_KEY:
        genai.configure(api_key=API_KEY)

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
    
    print(f"🤖 Generating response for: '{chat_data.message}' in organization {organization_id}")
    
    # Detect the language of the user's question (English or Arabic)
    detected_language = detect_language(chat_data.message)
    print(f"🌍 Detected language: {detected_language}")
    
    # Search through uploaded documents (filtered by organization)
    # The vector database now supports English and Arabic document search
    search_results = search_documents(chat_data.message, organization_id)
    print(f"📋 Search returned {len(search_results)} document results")
    
    # Debug: Print search results for troubleshooting
    for i, result in enumerate(search_results):
        print(f"  Result {i+1}: {result['filename']} (relevance: {result['relevance']:.3f})")
        print(f"    Chunks: {len(result['chunks'])}")
        if result['chunks']:
            print(f"    Sample chunk: {result['chunks'][0][:100]}...")
    
    # Prepare context from documents
    document_context = ""
    sources = []
    
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
                
                relevant_sources.append({
                    "document_id": result['document_id'],
                    "filename": result['filename'],
                    "relevance": result['relevance']
                })
        
        sources = relevant_sources  # Only include highly relevant sources
        print(f"📄 Using context from {len(sources)} highly relevant documents")
    else:
        print("⚠️ No relevant documents found")
        document_context = f"\n\nNo relevant information found in uploaded documents."
    
    # Generate response using Gemini with enhanced English/Arabic language prompt
    try:
        if API_KEY:
            model = genai.GenerativeModel("gemini-1.5-flash")
            
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
            
            # Clean up any remaining Markdown formatting to ensure plain text
            # This removes asterisks, bold formatting, and converts any remaining Markdown to clean text
            # Remove Markdown formatting
            ai_response = re.sub(r'\*\*([^*]+)\*\*', r'\1', ai_response)  # Remove **bold**
            ai_response = re.sub(r'\*([^*]+)\*', r'\1', ai_response)       # Remove *italic*
            ai_response = re.sub(r'^\s*\*\s*', '- ', ai_response)          # Convert leading * to -
            ai_response = re.sub(r'\n\s*\*\s*', '\n- ', ai_response)       # Convert * to - in middle
            ai_response = re.sub(r'^\s*-\s*', '', ai_response)             # Remove leading -
            ai_response = re.sub(r'\n\s*-\s*', '\n', ai_response)          # Remove - in middle
            # Clean up extra whitespace
            ai_response = re.sub(r'\n\s*\n\s*\n', '\n\n', ai_response)     # Remove excessive line breaks
            ai_response = ai_response.strip()
            
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
                ai_response = re.sub(r'\*\*([^*]+)\*\*', r'\1', ai_response)  # Remove **bold**
                ai_response = re.sub(r'\*([^*]+)\*', r'\1', ai_response)       # Remove *italic*
                ai_response = re.sub(r'^\s*\*\s*', '- ', ai_response)          # Convert leading * to -
                ai_response = re.sub(r'\n\s*\*\s*', '\n- ', ai_response)       # Convert * to - in middle
                ai_response = re.sub(r'^\s*-\s*', '', ai_response)             # Remove leading -
                ai_response = re.sub(r'\n\s*-\s*', '\n', ai_response)          # Remove - in middle
                # Clean up extra whitespace
                ai_response = re.sub(r'\n\s*\n\s*\n', '\n\n', ai_response)     # Remove excessive line breaks
                ai_response = ai_response.strip()
            
        else:
            ai_response = f"I'm a demo RAG chatbot. The Gemini API is not configured, so this is a mock response. Please configure the GOOGLE_API_KEY environment variable to enable AI responses."
    
    except Exception as e:
        ai_response = f"AI service temporarily unavailable: {str(e)}"
    
    # Mock session ID if not provided
    session_id = chat_data.session_id or 1
    
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
        message_id=12345,  # Mock message ID
        sources=sources,
        confidence=confidence,
        chunks_found=len(search_results)
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
