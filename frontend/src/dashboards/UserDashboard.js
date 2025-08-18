import React, { useState, useEffect } from "react";
import UserProfile from "../components/UserProfile";
import OrganizationInfo from "../components/OrganizationInfo";
import Chat from "../Chat";
import Documents from "../Documents";
import Settings from "../Settings";
import { getMyOrganization } from "../api";
import "./UserDashboard.css";

const UserDashboard = ({ user, onLogout }) => {
  const [activeTab, setActiveTab] = useState("profile");
  const [userInfo, setUserInfo] = useState(null);
  const [adminInfo, setAdminInfo] = useState(null);
  const [organizationInfo, setOrganizationInfo] = useState(null);

  useEffect(() => {
    // Load user and admin info
    loadUserInfo();
    loadAdminInfo();
    loadOrganizationInfo();
  }, []);

  const loadUserInfo = async () => {
    try {
      // You can add API call here to get detailed user info
      setUserInfo({
        id: user.id,
        email: user.email,
        fullName: "Your Name", // This should come from API
        role: "Member", // This should come from API
        createdAt: new Date().toLocaleDateString(),
      });
    } catch (error) {
      console.error("Error loading user info:", error);
    }
  };

  const loadAdminInfo = async () => {
    try {
      // You can add API call here to get admin info
      setAdminInfo({
        id: user.admin_id,
        name: "Your Admin", // This should come from API
        email: "admin@example.com", // This should come from API
      });
    } catch (error) {
      console.error("Error loading admin info:", error);
    }
  };

  const loadOrganizationInfo = async () => {
    try {
      // Fetch organization info using the new endpoint
      const orgData = await getMyOrganization();
      setOrganizationInfo({
        id: orgData.organization_id,
        name: orgData.name,
      });
    } catch (error) {
      console.error("Error loading organization info:", error);
      // Fallback to a default name
      setOrganizationInfo({
        id: user.organization_id,
        name: "Organization",
      });
    }
  };

  return (
    <div className="user-dashboard">
      {/* Header */}
      <header className="dashboard-header">
        <div className="header-content">
          <div className="user-info">
            <h1>User Dashboard</h1>
            <p>Welcome, {user.full_name}</p>
            {userInfo && <p className="user-role">Role: {userInfo.role}</p>}
          </div>
          <div className="header-actions">
            <button onClick={onLogout} className="btn btn-secondary">
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Info Cards */}
      <div className="info-section">
        <div className="info-grid">
          <div className="info-card">
            <h3>Your Organization</h3>
            <p className="info-text">
              {organizationInfo?.name || "Loading..."}
            </p>
          </div>
          <div className="info-card">
            <h3>Your Admin</h3>
            <p className="info-text">Admin ID: {user.admin_id}</p>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="dashboard-tabs">
        <button
          className={`tab-button ${activeTab === "profile" ? "active" : ""}`}
          onClick={() => setActiveTab("profile")}
        >
          👤 Profile
        </button>
        <button
          className={`tab-button ${activeTab === "chatbot" ? "active" : ""}`}
          onClick={() => setActiveTab("chatbot")}
        >
          🤖 Chatbot
        </button>
        <button
          className={`tab-button ${activeTab === "documents" ? "active" : ""}`}
          onClick={() => setActiveTab("documents")}
        >
          📁 Documents
        </button>
        <button
          className={`tab-button ${activeTab === "settings" ? "active" : ""}`}
          onClick={() => setActiveTab("settings")}
        >
          ⚙️ Settings
        </button>
      </div>

      {/* Content Area */}
      <div className="dashboard-content">
        {activeTab === "profile" && <UserProfile userInfo={userInfo} />}
        {activeTab === "chatbot" && <Chat />}
        {activeTab === "documents" && <Documents user={user} />}
        {activeTab === "settings" && <Settings />}
      </div>
    </div>
  );
};

export default UserDashboard;
