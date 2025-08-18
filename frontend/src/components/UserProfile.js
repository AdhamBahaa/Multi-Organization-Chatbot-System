import React from "react";
import "./UserProfile.css";

const UserProfile = ({ userInfo }) => {
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
            <label>Role:</label>
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
            <button className="btn btn-primary">Edit Profile</button>
            <button className="btn btn-secondary">Change Password</button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UserProfile;
