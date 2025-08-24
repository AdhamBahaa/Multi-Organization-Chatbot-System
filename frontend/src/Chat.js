import React, { useState, useRef, useEffect } from "react";
import { sendMessage } from "./api";
import "./Chat.css";

function Chat() {
  const [messages, setMessages] = useState([
    {
      id: 1,
      content:
        "Hello! I'm your AI-powered RAG chatbot assistant. I can help you find information from your uploaded documents. Simply ask me anything and I'll search through your documents to provide accurate answers.",
      role: "assistant",
      timestamp: new Date(),
    },
  ]);
  const [inputMessage, setInputMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, []);

  useEffect(() => {
    console.log(
      "Session ID changed:",
      currentSessionId,
      typeof currentSessionId
    );
  }, [currentSessionId]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim() || loading) return;

    const userMessage = {
      id: Date.now(),
      content: inputMessage,
      role: "user",
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputMessage("");
    setLoading(true);
    setError(null);

    try {
      const response = await sendMessage(inputMessage, currentSessionId);

      // Ensure response exists and has required properties
      if (!response) {
        throw new Error("No response received from the server");
      }

      // Update session ID if this is the first message
      if (!currentSessionId && response.session_id) {
        console.log(
          "Setting new session ID:",
          response.session_id,
          typeof response.session_id
        );
        setCurrentSessionId(response.session_id);
      }

      const botMessage = {
        id: response.message_id || Date.now(),
        content:
          response.response ||
          "I'm sorry, I couldn't generate a response. Please try again.",
        role: "assistant",
        timestamp: new Date(),
        confidence: response.confidence,
        sources: response.sources || [],
        chunks_found: response.chunks_found || 0,
      };

      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      console.error("Chat error:", error);
      setError(error.message);

      const errorMessage = {
        id: Date.now() + 1,
        content:
          "Sorry, I encountered an error while processing your request. Please try again or check your connection.",
        role: "assistant",
        timestamp: new Date(),
        isError: true,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const clearChat = () => {
    console.log("Clearing chat, current session ID:", currentSessionId);
    setMessages([
      {
        id: 1,
        content:
          "Hello! I'm your AI-powered RAG chatbot assistant. I can help you find information from your uploaded documents. Simply ask me anything and I'll search through your documents to provide accurate answers.",
        role: "assistant",
        timestamp: new Date(),
      },
    ]);
    setCurrentSessionId(null);
    setError(null);
    console.log("Chat cleared, session ID reset to:", null);
  };

  const formatTime = (date) => {
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.8) return "high";
    if (confidence >= 0.6) return "medium";
    return "low";
  };

  const getConfidenceLabel = (confidence) => {
    if (confidence >= 0.8) return "High";
    if (confidence >= 0.6) return "Medium";
    return "Low";
  };

  const formatSessionId = (sessionId) => {
    if (!sessionId) return "";
    if (typeof sessionId !== "string") return String(sessionId);
    if (sessionId.length <= 8) return sessionId;
    return `${sessionId.slice(0, 8)}...`;
  };

  return (
    <div className="chat-container">
      {/* Enhanced Header */}
      <div className="chat-header">
        <div className="chat-header-left">
          <div className="chat-title">
            <div className="chat-icon">🤖</div>
            <div>
              <h2>AI Chat Assistant</h2>
              <p className="chat-subtitle">Powered by RAG Technology</p>
            </div>
          </div>
        </div>
        <div className="chat-header-right">
          <button
            onClick={clearChat}
            className="clear-chat-btn"
            title="Clear conversation history"
          >
            <span className="btn-icon">🗑️</span>
            <span className="btn-text">Clear Chat</span>
          </button>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="error-banner">
          <div className="error-icon">⚠️</div>
          <div className="error-content">
            <strong>Error:</strong> {error}
          </div>
        </div>
      )}

      {/* Messages Container */}
      <div className="messages-container">
        {messages.map((message) => (
          <div key={message.id} className={`message-wrapper ${message.role}`}>
            <div
              className={`message ${message.role} ${
                message.isError ? "error" : ""
              }`}
            >
              {/* Message Avatar */}
              <div className="message-avatar">
                {message.role === "user" ? "👤" : "🤖"}
              </div>

              {/* Message Content */}
              <div className="message-content">
                <div className="message-text">{message.content}</div>

                {/* Sources Section */}
                {message.sources && message.sources.length > 0 && (
                  <div className="message-sources">
                    <div className="sources-header">
                      <span className="sources-icon">📄</span>
                      <strong>Sources Found:</strong>
                    </div>
                    <div className="sources-list">
                      {message.sources.map((source, idx) => (
                        <div key={idx} className="source-item">
                          <div className="source-filename">
                            {source.filename}
                            {source.page_number && (
                              <span className="source-page">
                                {" "}
                                (Page {source.page_number})
                              </span>
                            )}
                          </div>
                          {source.similarity_score && (
                            <div className="source-match">
                              {Math.round(source.similarity_score * 100)}% match
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Message Footer */}
                <div className="message-footer">
                  <span className="message-time">
                    {formatTime(message.timestamp)}
                  </span>

                  {message.confidence !== undefined && (
                    <div
                      className={`confidence-badge confidence-${getConfidenceColor(
                        message.confidence
                      )}`}
                    >
                      {getConfidenceLabel(message.confidence)} Confidence
                    </div>
                  )}

                  {message.chunks_found > 0 && (
                    <div className="chunks-info">
                      📊 {message.chunks_found} relevant chunks found
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}

        {/* Loading Indicator */}
        {loading && (
          <div className="message-wrapper assistant">
            <div className="message assistant loading">
              <div className="message-avatar">🤖</div>
              <div className="message-content">
                <div className="typing-indicator">
                  <div className="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                  <span className="typing-text">AI is thinking...</span>
                </div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Enhanced Input Form */}
      <form onSubmit={handleSend} className="chat-input-form">
        <div className="input-container">
          <input
            ref={inputRef}
            type="text"
            className="chat-input"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            placeholder="Ask me anything about your uploaded documents..."
            disabled={loading}
            maxLength={500}
          />
          <div className="input-actions">
            <div className="char-count">{inputMessage.length}/500</div>
            <button
              type="submit"
              className="send-button"
              disabled={!inputMessage.trim() || loading}
              title={
                !inputMessage.trim() ? "Please enter a message" : "Send message"
              }
            >
              {loading ? (
                <span className="send-loading">
                  <div className="send-spinner"></div>
                </span>
              ) : (
                <>
                  <span className="send-icon">📤</span>
                  <span className="send-text">Send</span>
                </>
              )}
            </button>
          </div>
        </div>
      </form>

      {/* Session Info */}
      {currentSessionId && (
        <div className="session-info">
          <div className="session-badge">
            <span className="session-icon">🔗</span>
            Session: {formatSessionId(currentSessionId)}
          </div>
        </div>
      )}

      {/* Quick Tips */}
      <div className="quick-tips">
        <div className="tips-header">
          <span className="tips-icon">💡</span>
          <strong>Quick Tips:</strong>
        </div>
        <div className="tips-content">
          <span className="tip">Ask specific questions for better results</span>
          <span className="tip">
            I can search through all your uploaded documents
          </span>
          <span className="tip">Available in English and Arabic</span>
        </div>
      </div>
    </div>
  );
}

export default Chat;
