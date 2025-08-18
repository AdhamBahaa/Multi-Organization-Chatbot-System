"""
Chat functionality module for the RAG Chatbot Backend
"""
import google.generativeai as genai
from .models import ChatRequest, ChatResponse
from .utils import search_documents
from .config import API_KEY

def configure_gemini():
    """Configure Gemini API if key is available"""
    if API_KEY:
        genai.configure(api_key=API_KEY)

async def generate_chat_response(chat_data: ChatRequest) -> ChatResponse:
    """Generate AI-powered response with RAG functionality"""
    
    print(f"🤖 Generating response for: '{chat_data.message}'")
    
    # Search through uploaded documents
    search_results = search_documents(chat_data.message)
    print(f"📋 Search returned {len(search_results)} document results")
    
    # Prepare context from documents
    document_context = ""
    sources = []
    
    if search_results:
        document_context = "\n\nRelevant information from uploaded documents:\n"
        for result in search_results[:2]:  # Use top 2 most relevant documents
            document_context += f"\nFrom {result['filename']}:\n"
            for chunk in result['chunks']:
                if chunk.strip():
                    document_context += f"- {chunk.strip()}\n"
            
            sources.append({
                "document_id": result['document_id'],
                "filename": result['filename'],
                "relevance": result['relevance']
            })
        
        print(f"📄 Using context from {len(sources)} documents")
    else:
        print("⚠️ No relevant documents found")
        document_context = "\n\nNo relevant information found in uploaded documents."
    
    # Generate response using Gemini with document context
    try:
        if API_KEY:
            model = genai.GenerativeModel("gemini-1.5-flash")
            
            prompt = f"""You are a helpful RAG chatbot assistant. Answer the user's question based on the provided context from their uploaded documents.

User Question: {chat_data.message}

{document_context}

Instructions:
- If the document context contains relevant information, use it to answer the question
- If no relevant information is found in the documents, provide a general helpful response
- Be specific and reference the information from the documents when applicable
- If you mention information from documents, indicate which document it came from
"""
            
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=500,
                )
            )
            ai_response = response.text.strip()
        else:
            ai_response = "I'm a demo RAG chatbot. The Gemini API is not configured, so this is a mock response. Please configure the GOOGLE_API_KEY environment variable to enable AI responses."
    
    except Exception as e:
        ai_response = f"AI service temporarily unavailable: {str(e)}"
    
    # Mock session ID if not provided
    session_id = chat_data.session_id or 1
    
    return ChatResponse(
        response=ai_response,
        session_id=session_id,
        message_id=12345,  # Mock message ID
        sources=sources,
        confidence=0.8 if search_results else 0.5,
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
