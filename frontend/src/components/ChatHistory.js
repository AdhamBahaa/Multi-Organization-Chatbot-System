import React, { useState, useEffect } from "react";
import { getUserSessions, getSessionHistory, deleteSession } from "../api";
import "./ChatHistory.css";

const ChatHistory = ({ onLoadSession, currentSessionId, onClose }) => {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedSession, setSelectedSession] = useState(null);
  const [sessionMessages, setSessionMessages] = useState([]);
  const [loadingMessages, setLoadingMessages] = useState(false);

  useEffect(() => {
    loadSessions();
  }, []);

  const loadSessions = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getUserSessions();
      setSessions(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadSessionMessages = async (sessionId) => {
    try {
      setLoadingMessages(true);
      setError(null);
      const data = await getSessionHistory(sessionId);
      setSessionMessages(data.messages);
      setSelectedSession(data.session);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoadingMessages(false);
    }
  };

  const handleSessionClick = async (sessionId) => {
    await loadSessionMessages(sessionId);
  };

  const handleLoadSession = () => {
    if (selectedSession) {
      onLoadSession(selectedSession.session_id, sessionMessages);
    }
  };

  const handleDeleteSession = async (sessionId, event) => {
    event.stopPropagation();
    if (
      window.confirm(
        "Are you sure you want to delete this conversation? This action cannot be undone."
      )
    ) {
      try {
        await deleteSession(sessionId);
        // Remove from sessions list
        setSessions(sessions.filter((s) => s.session_id !== sessionId));
        // Clear selected session if it was the deleted one
        if (selectedSession && selectedSession.session_id === sessionId) {
          setSelectedSession(null);
          setSessionMessages([]);
        }
      } catch (err) {
        setError(err.message);
      }
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return (
      date.toLocaleDateString() +
      " " +
      date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    );
  };

  const formatMessagePreview = (content) => {
    // Remove extra whitespace and newlines
    const cleanContent = content.replace(/\s+/g, " ").trim();
    return cleanContent.length > 80
      ? cleanContent.substring(0, 80) + "..."
      : cleanContent;
  };

  if (loading) {
    return (
      <div className="chat-history">
        <div className="chat-history-header">
          <h3>💬 Chat History</h3>
        </div>
        <div className="chat-history-loading">
          <div className="spinner"></div>
          <p>Loading your conversations...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="chat-history">
      <div className="chat-history-header">
        <h3>💬 Chat History</h3>
        <div className="header-actions">
          <button
            className="refresh-btn"
            onClick={loadSessions}
            title="Refresh conversations"
          >
            🔄
          </button>
          <button
            className="close-btn"
            onClick={onClose}
            title="Close chat history"
          >
            ✕
          </button>
        </div>
      </div>

      {error && (
        <div className="chat-history-error">
          <p>❌ {error}</p>
          <button onClick={loadSessions}>Try Again</button>
        </div>
      )}

      {sessions.length === 0 ? (
        <div className="chat-history-empty">
          <p>📝 No conversations yet</p>
          <p>Start chatting to see your history here!</p>
        </div>
      ) : (
        <div className="chat-history-content">
          <div className="sessions-list">
            <h4>Your Conversations</h4>
            {sessions.map((session) => (
              <div
                key={session.session_id}
                className={`session-item ${
                  selectedSession?.session_id === session.session_id
                    ? "selected"
                    : ""
                } ${currentSessionId === session.session_id ? "current" : ""}`}
                onClick={() => handleSessionClick(session.session_id)}
              >
                <div className="session-info">
                  <div className="session-title">{session.title}</div>
                  <div className="session-meta">
                    <span className="session-date">
                      {formatDate(session.updated_at)}
                    </span>
                    <span className="session-count">
                      {session.message_count} messages
                    </span>
                  </div>
                </div>
                <button
                  className="delete-session-btn"
                  onClick={(e) => handleDeleteSession(session.session_id, e)}
                  title="Delete conversation"
                >
                  🗑️
                </button>
              </div>
            ))}
          </div>

          {selectedSession && (
            <div className="session-details">
              <div className="session-header">
                <h4>{selectedSession.title}</h4>
                <button
                  className="load-session-btn"
                  onClick={handleLoadSession}
                  disabled={currentSessionId === selectedSession.session_id}
                >
                  {currentSessionId === selectedSession.session_id
                    ? "✓ Current Session"
                    : "📥 Load Session"}
                </button>
              </div>

              {loadingMessages ? (
                <div className="messages-loading">
                  <div className="spinner"></div>
                  <p>Loading messages...</p>
                </div>
              ) : (
                <div className="messages-preview">
                  {sessionMessages.slice(-6).map((message) => (
                    <div
                      key={message.message_id}
                      className={`message-preview ${message.role}`}
                    >
                      <div className="message-role">
                        {message.role === "user" ? "👤 You" : "🤖 Assistant"}
                      </div>
                      <div className="message-content">
                        {formatMessagePreview(message.content)}
                      </div>
                      <div className="message-time">
                        {formatDate(message.timestamp)}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ChatHistory;
