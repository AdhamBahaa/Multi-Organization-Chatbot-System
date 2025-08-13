import React, { useState, useRef, useEffect } from 'react';
import { sendMessage, getChatSessions } from './api';

function Chat() {
  const [messages, setMessages] = useState([
    {
      id: 1,
      content: "Hello! I'm your RAG chatbot assistant. Upload some documents and I'll help you find information from them.",
      role: 'assistant',
      timestamp: new Date()
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim() || loading) return;

    const userMessage = {
      id: Date.now(),
      content: inputMessage,
      role: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setLoading(true);
    setError(null);

    try {
      const response = await sendMessage(inputMessage, currentSessionId);
      
      // Update session ID if this is the first message
      if (!currentSessionId) {
        setCurrentSessionId(response.session_id);
      }
      
      const botMessage = {
        id: response.message_id,
        content: response.response,
        role: 'assistant',
        timestamp: new Date(),
        confidence: response.confidence,
        sources: response.sources || [],
        chunks_found: response.chunks_found || 0
      };
      
      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('Chat error:', error);
      setError(error.message);
      
      const errorMessage = {
        id: Date.now() + 1,
        content: "Sorry, I encountered an error. Please try again.",
        role: 'assistant',
        timestamp: new Date(),
        isError: true
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const clearChat = () => {
    setMessages([
      {
        id: 1,
        content: "Hello! I'm your RAG chatbot assistant. Upload some documents and I'll help you find information from them.",
        role: 'assistant',
        timestamp: new Date()
      }
    ]);
    setCurrentSessionId(null);
    setError(null);
  };

  const formatTime = (date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h2 style={{ margin: 0 }}>Chat Assistant</h2>
        <button onClick={clearChat} className="button" style={{ background: 'rgba(239, 68, 68, 0.1)', color: '#dc2626', border: '1px solid rgba(239, 68, 68, 0.2)' }}>
          Clear Chat
        </button>
      </div>
      
      {error && (
        <div style={{ 
          background: 'rgba(239, 68, 68, 0.1)', 
          color: '#dc2626', 
          padding: '10px', 
          borderRadius: '6px', 
          marginBottom: '15px',
          fontSize: '14px'
        }}>
          Error: {error}
        </div>
      )}
      
      <div style={{
        height: '400px', 
        overflowY: 'auto', 
        border: '1px solid #e5e7eb', 
        borderRadius: '6px', 
        padding: '15px', 
        marginBottom: '15px', 
        background: '#fafafa'
      }}>
        {messages.map((message) => (
          <div key={message.id} className={`message ${message.role}`}>
            <div style={{marginBottom: '5px', lineHeight: '1.5'}}>
              {message.content}
            </div>
            
            {/* Show sources if available */}
            {message.sources && message.sources.length > 0 && (
              <div style={{
                marginTop: '10px',
                padding: '8px',
                background: 'rgba(59, 130, 246, 0.1)',
                borderRadius: '4px',
                fontSize: '12px'
              }}>
                <strong>Sources:</strong>
                {message.sources.map((source, idx) => (
                  <div key={idx} style={{ marginTop: '4px' }}>
                    📄 {source.filename} {source.page_number && `(Page ${source.page_number})`}
                    {source.similarity_score && ` - ${Math.round(source.similarity_score * 100)}% match`}
                  </div>
                ))}
              </div>
            )}
            
            <div style={{fontSize: '12px', opacity: 0.7, marginTop: '5px'}}>
              {formatTime(message.timestamp)}
              {message.confidence !== undefined && ` • Confidence: ${Math.round(message.confidence * 100)}%`}
              {message.chunks_found > 0 && ` • Found ${message.chunks_found} relevant chunks`}
            </div>
          </div>
        ))}
        
        {loading && (
          <div className="message assistant">
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div style={{ 
                width: '20px', 
                height: '20px', 
                border: '2px solid #f3f3f3', 
                borderTop: '2px solid #3498db', 
                borderRadius: '50%',
                animation: 'spin 1s linear infinite'
              }}></div>
              Thinking...
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
      <form onSubmit={handleSend} style={{display: 'flex', gap: '10px'}}>
        <input
          type="text"
          className="input"
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          placeholder="Ask me anything about your uploaded documents..."
          disabled={loading}
          style={{ flex: 1 }}
        />
        <button type="submit" className="button" disabled={!inputMessage.trim() || loading}>
          {loading ? '...' : 'Send'}
        </button>
      </form>
      
      {currentSessionId && (
        <div style={{ 
          fontSize: '12px', 
          color: '#6b7280', 
          marginTop: '10px',
          textAlign: 'center'
        }}>
          Session ID: {currentSessionId}
        </div>
      )}
    </div>
  );
}

export default Chat;
