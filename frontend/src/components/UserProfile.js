import React, { useState } from "react";
import { changePassword } from "../api";
import "./UserProfile.css";

// Password validation function
const validatePasswordStrength = (password) => {
  if (password.length < 8) {
    return {
      isValid: false,
      message: "Password must be at least 8 characters long",
    };
  }

  if (password.length > 128) {
    return {
      isValid: false,
      message: "Password must be no more than 128 characters long",
    };
  }

  if (!/[A-Z]/.test(password)) {
    return {
      isValid: false,
      message: "Password must contain at least one uppercase letter (A-Z)",
    };
  }

  if (!/[a-z]/.test(password)) {
    return {
      isValid: false,
      message: "Password must contain at least one lowercase letter (a-z)",
    };
  }

  if (!/\d/.test(password)) {
    return {
      isValid: false,
      message: "Password must contain at least one number (0-9)",
    };
  }

  // Check for special characters using a safer approach
  const specialChars = "!@#$%^&*()_+-=[]{}|;:,.<>?";
  const hasSpecialChar = [...specialChars].some((char) =>
    password.includes(char)
  );
  if (!hasSpecialChar) {
    return {
      isValid: false,
      message:
        "Password must contain at least one special character (!@#$%^&*()_+-=[]{}|;:,.<>&gt;?)",
    };
  }

  return { isValid: true, message: "Password meets all strength requirements" };
};

// Helper function to check if password has special characters
const hasSpecialCharacters = (password) => {
  const specialChars = "!@#$%^&*()_+-=[]{}|;:,.<>?";
  return [...specialChars].some((char) => password.includes(char));
};

const UserProfile = ({ userInfo }) => {
  const [showChangePassword, setShowChangePassword] = useState(false);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const handleChangePassword = async (e) => {
    e.preventDefault();

    if (newPassword !== confirmPassword) {
      setMessage("New passwords do not match");
      return;
    }

    // Strong password validation
    const passwordValidation = validatePasswordStrength(newPassword);
    if (!passwordValidation.isValid) {
      setMessage(passwordValidation.message);
      return;
    }

    setLoading(true);

    try {
      await changePassword(currentPassword, newPassword);
      setMessage(
        "Password changed successfully! A confirmation email has been sent to your email address."
      );
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setTimeout(() => {
        setShowChangePassword(false);
        setMessage("");
      }, 2000);
    } catch (error) {
      setMessage(error.message || "Failed to change password");
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    setShowChangePassword(false);
    setCurrentPassword("");
    setNewPassword("");
    setConfirmPassword("");
    setMessage("");
  };

  // Add null checking for userInfo
  if (!userInfo) {
    return (
      <div className="user-profile">
        <div className="profile-header">
          <h2>User Profile</h2>
        </div>
        <div className="profile-info">
          <p>Loading user information...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="user-profile">
      <div className="profile-header">
        <h2>User Profile</h2>
        <button
          className="btn btn-primary"
          onClick={() => setShowChangePassword(true)}
        >
          Change Password
        </button>
      </div>

      <div className="profile-info">
        <div className="info-row">
          <label>Full Name:</label>
          <span>{userInfo.full_name}</span>
        </div>
        <div className="info-row">
          <label>Email:</label>
          <span>{userInfo.email}</span>
        </div>
        <div className="info-row">
          <label>Role:</label>
          <span>User</span>
        </div>
        <div className="info-row">
          <label>Organization ID:</label>
          <span>{userInfo.organization_id}</span>
        </div>
      </div>

      {/* Change Password Modal */}
      {showChangePassword && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h3>Change Password</h3>
              <button className="close-btn" onClick={handleCancel}>
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
                  placeholder="Enter current password"
                />
              </div>
              <div className="form-group">
                <label>New Password:</label>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  required
                  placeholder="Enter new password"
                />
                <div className="password-requirements">
                  <small>Password must contain:</small>
                  <ul>
                    <li
                      className={newPassword.length >= 8 ? "valid" : "invalid"}
                    >
                      At least 8 characters
                    </li>
                    <li
                      className={
                        /[A-Z]/.test(newPassword) ? "valid" : "invalid"
                      }
                    >
                      One uppercase letter (A-Z)
                    </li>
                    <li
                      className={
                        /[a-z]/.test(newPassword) ? "valid" : "invalid"
                      }
                    >
                      One lowercase letter (a-z)
                    </li>
                    <li
                      className={/\d/.test(newPassword) ? "valid" : "invalid"}
                    >
                      One number (0-9)
                    </li>
                    <li
                      className={
                        hasSpecialCharacters(newPassword) ? "valid" : "invalid"
                      }
                    >
                      One special character (!@#$%^&amp;*()_+-=[]{}
                      |;:,.&lt;&gt;?)
                    </li>
                  </ul>
                </div>
              </div>
              <div className="form-group">
                <label>Confirm New Password:</label>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  placeholder="Confirm new password"
                />
              </div>
              {message && (
                <div
                  className={
                    message.includes("successfully")
                      ? "success-message"
                      : "error-message"
                  }
                >
                  {message}
                </div>
              )}
              <div className="modal-actions">
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={handleCancel}
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
