import React, { useState, useEffect } from "react";
import { getUsersFeedback, getFeedbackStats } from "../api";
import "./FeedbackManager.css";

function FeedbackManager() {
  const [feedback, setFeedback] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filterRating, setFilterRating] = useState("all");
  const [sortBy, setSortBy] = useState("date");

  useEffect(() => {
    loadFeedback();
  }, []);

  const loadFeedback = async () => {
    try {
      setLoading(true);
      const [feedbackData, statsData] = await Promise.all([
        getUsersFeedback(),
        getFeedbackStats(),
      ]);
      setFeedback(feedbackData);
      setStats(statsData);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getRatingColor = (rating) => {
    if (rating >= 4) return "excellent";
    if (rating >= 3) return "good";
    if (rating >= 2) return "fair";
    return "poor";
  };

  const getRatingLabel = (rating) => {
    const labels = {
      1: "Poor",
      2: "Fair",
      3: "Good",
      4: "Very Good",
      5: "Excellent",
    };
    return labels[rating] || "Unknown";
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  const filteredFeedback = feedback.filter((item) => {
    if (filterRating === "all") return true;
    return item.rating === parseInt(filterRating);
  });

  const sortedFeedback = [...filteredFeedback].sort((a, b) => {
    switch (sortBy) {
      case "date":
        return new Date(b.created_at) - new Date(a.created_at);
      case "rating":
        return b.rating - a.rating;
      case "user":
        return a.user_name.localeCompare(b.user_name);
      default:
        return 0;
    }
  });

  if (loading) {
    return (
      <div className="feedback-manager">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading feedback data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="feedback-manager">
        <div className="error-container">
          <div className="error-icon">⚠️</div>
          <h3>Error Loading Feedback</h3>
          <p>{error}</p>
          <button onClick={loadFeedback} className="retry-button">
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="feedback-manager">
      <div className="feedback-header">
        <h2>User Feedback Management</h2>
        <button onClick={loadFeedback} className="refresh-button">
          🔄 Refresh
        </button>
      </div>

      {/* Statistics Section */}
      {stats && (
        <div className="stats-section">
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-number">{stats.total_feedback}</div>
              <div className="stat-label">Total Feedback</div>
            </div>
            <div className="stat-card">
              <div className="stat-number">
                {stats.average_rating.toFixed(1)}
              </div>
              <div className="stat-label">Average Rating</div>
            </div>
            <div className="stat-card">
              <div className="stat-number">{stats.total_users}</div>
              <div className="stat-label">Active Users</div>
            </div>
          </div>

          {/* Rating Distribution */}
          <div className="rating-distribution">
            <h4>Rating Distribution</h4>
            <div className="rating-bars">
              {[5, 4, 3, 2, 1].map((rating) => (
                <div key={rating} className="rating-bar-item">
                  <div className="rating-label">
                    {rating} ★ ({getRatingLabel(rating)})
                  </div>
                  <div className="rating-bar-container">
                    <div
                      className="rating-bar-fill"
                      style={{
                        width: `${
                          stats.total_feedback > 0
                            ? (stats.rating_distribution[rating] /
                                stats.total_feedback) *
                              100
                            : 0
                        }%`,
                        backgroundColor:
                          rating >= 4
                            ? "#48bb78"
                            : rating >= 3
                            ? "#ed8936"
                            : "#e53e3e",
                      }}
                    ></div>
                  </div>
                  <div className="rating-count">
                    {stats.rating_distribution[rating]}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Filters and Controls */}
      <div className="feedback-controls">
        <div className="filter-section">
          <label htmlFor="rating-filter">Filter by Rating:</label>
          <select
            id="rating-filter"
            value={filterRating}
            onChange={(e) => setFilterRating(e.target.value)}
          >
            <option value="all">All Ratings</option>
            <option value="5">5 Stars (Excellent)</option>
            <option value="4">4 Stars (Very Good)</option>
            <option value="3">3 Stars (Good)</option>
            <option value="2">2 Stars (Fair)</option>
            <option value="1">1 Star (Poor)</option>
          </select>
        </div>

        <div className="sort-section">
          <label htmlFor="sort-by">Sort by:</label>
          <select
            id="sort-by"
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
          >
            <option value="date">Date (Newest First)</option>
            <option value="rating">Rating (Highest First)</option>
            <option value="user">User Name</option>
          </select>
        </div>
      </div>

      {/* Feedback List */}
      <div className="feedback-list">
        {sortedFeedback.length === 0 ? (
          <div className="no-feedback">
            <div className="no-feedback-icon">📝</div>
            <h3>No Feedback Found</h3>
            <p>No feedback matches your current filters.</p>
          </div>
        ) : (
          sortedFeedback.map((item) => (
            <div key={item.feedback_id} className="feedback-item">
              <div className="feedback-header-row">
                <div className="feedback-user-info">
                  <div className="user-name">{item.user_name}</div>
                  <div className="user-role">{item.user_role}</div>
                </div>
                <div className="feedback-rating">
                  <div
                    className={`rating-badge rating-${getRatingColor(
                      item.rating
                    )}`}
                  >
                    {item.rating} ★ {getRatingLabel(item.rating)}
                  </div>
                </div>
                <div className="feedback-date">
                  {formatDate(item.created_at)}
                </div>
              </div>

              <div className="feedback-content">
                <div className="conversation-preview">
                  <div className="user-message">
                    <strong>User:</strong> {item.user_message}
                  </div>
                  <div className="bot-response">
                    <strong>Bot:</strong> {item.bot_response}
                  </div>
                </div>

                {item.comment && (
                  <div className="feedback-comment">
                    <strong>Comment:</strong> {item.comment}
                  </div>
                )}

                <div className="feedback-metadata">
                  <span className="session-info">
                    Session: {item.session_id} | Message: {item.message_id}
                  </span>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default FeedbackManager;
