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

async def generate_chat_response(chat_data: ChatRequest, organization_id: int = None) -> ChatResponse:
    """Generate AI-powered response with RAG functionality"""
    
    print(f"🤖 Generating response for: '{chat_data.message}' in organization {organization_id}")
    
    # Search through uploaded documents (filtered by organization)
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
        document_context = "\n\nRelevant information from uploaded documents:\n"
        
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
        document_context = "\n\nNo relevant information found in uploaded documents."
    
    # Generate response using Gemini with document context
    try:
        if API_KEY:
            model = genai.GenerativeModel("gemini-1.5-flash")
            
            prompt = f"""You are a helpful RAG chatbot assistant. Answer the user's question based on the provided context from their uploaded documents.

CORE RULE: Respond in the SAME LANGUAGE as the user's question.

User Question: {chat_data.message}

{document_context}

Instructions:
- If the document context contains relevant information, use it to answer the question
- If no relevant information is found in the documents, provide a general helpful response
- Be specific and reference the information from the documents when applicable
- If you mention information from documents, indicate which document it came from
- Detect the question language and respond in that language
"""
            
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,  # Lower temperature for more consistent, accurate responses
                    max_output_tokens=800,  # Increased for more detailed responses
                    top_p=0.8,  # Add top_p for better response quality
                    top_k=40,   # Add top_k for better response quality
                )
            )
            ai_response = response.text.strip()
        else:
            ai_response = "I'm a demo RAG chatbot. The Gemini API is not configured, so this is a mock response. Please configure the GOOGLE_API_KEY environment variable to enable AI responses."
    
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
