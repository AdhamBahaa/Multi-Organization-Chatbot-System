import React, { useState } from "react";
import { changePassword } from "../api";
import "./UserProfile.css";

const UserProfile = ({ userInfo }) => {
  const [showChangePassword, setShowChangePassword] = useState(false);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const handleChangePassword = async (e) => {
    e.preventDefault();

    if (newPassword !== confirmPassword) {
      setMessage("New passwords do not match");
      return;
    }

    if (newPassword.length < 6) {
      setMessage("New password must be at least 6 characters long");
      return;
    }

    setLoading(true);
    setMessage("");

    try {
      await changePassword(currentPassword, newPassword);
      setMessage("Password changed successfully!");
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setTimeout(() => {
        setShowChangePassword(false);
        setMessage("");
      }, 2000);
    } catch (error) {
      setMessage(error.message);
    } finally {
      setLoading(false);
    }
  };

  const closeModal = () => {
    setShowChangePassword(false);
    setCurrentPassword("");
    setNewPassword("");
    setConfirmPassword("");
    setMessage("");
  };
  if (!userInfo) {
    return (
      <div className="user-profile">
        <div className="loading">Loading profile information...</div>
      </div>
    );
  }

  return (
    <div className="user-profile">
      <h2>Your Profile</h2>

      <div className="profile-card">
        <div className="profile-section">
          <h3>Personal Information</h3>
          <div className="profile-field">
            <label>Full Name:</label>
            <span>{userInfo.fullName}</span>
          </div>
          <div className="profile-field">
            <label>Email:</label>
            <span>{userInfo.email}</span>
          </div>
          <div className="profile-field">
            <label>Organization Role:</label>
            <span className="role-badge">{userInfo.role}</span>
          </div>
        </div>

        <div className="profile-section">
          <h3>Account Information</h3>
          <div className="profile-field">
            <label>User ID:</label>
            <span>{userInfo.id}</span>
          </div>
          <div className="profile-field">
            <label>Member Since:</label>
            <span>{userInfo.createdAt}</span>
          </div>
        </div>

        <div className="profile-section">
          <h3>Actions</h3>
          <div className="profile-actions">
            <button
              className="btn btn-secondary"
              onClick={() => setShowChangePassword(true)}
            >
              Change Password
            </button>
          </div>
        </div>
      </div>

      {/* Change Password Modal */}
      {showChangePassword && (
        <div className="modal-overlay" onClick={closeModal}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Change Password</h3>
              <button className="modal-close" onClick={closeModal}>
                ×
              </button>
            </div>
            <form onSubmit={handleChangePassword}>
              <div className="form-group">
                <label>Current Password:</label>
                <input
                  type="password"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  required
                  placeholder="Enter your current password"
                />
              </div>
              <div className="form-group">
                <label>New Password:</label>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  required
                  minLength={6}
                  placeholder="Enter new password (min 6 characters)"
                />
              </div>
              <div className="form-group">
                <label>Confirm New Password:</label>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  placeholder="Confirm your new password"
                />
              </div>
              {message && (
                <div
                  className={`message ${
                    message.includes("successfully") ? "success" : "error"
                  }`}
                >
                  {message}
                </div>
              )}
              <div className="modal-actions">
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={closeModal}
                  disabled={loading}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={loading}
                >
                  {loading ? "Changing..." : "Change Password"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default UserProfile;
