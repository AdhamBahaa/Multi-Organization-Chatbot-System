import React, { useState, useEffect, useCallback } from "react";
import UserManager from "../components/UserManager";
import OrganizationInfo from "../components/OrganizationInfo";
import AdminProfile from "../components/AdminProfile";
import Chat from "../Chat";
import Documents from "../Documents";
import Settings from "../Settings";
import { getMyOrganization } from "../api";
import "./AdminDashboard.css";

const AdminDashboard = ({ user, onLogout }) => {
  const [activeTab, setActiveTab] = useState("users");
  const [organizationInfo, setOrganizationInfo] = useState(null);
  const [stats, setStats] = useState({
    totalUsers: 0,
  });

  useEffect(() => {
    // Load organization info and stats
    loadOrganizationInfo();
    loadStats();
  }, []);

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

  const loadStats = async () => {
    try {
      // Stats will be updated by UserManager component
      setStats({
        totalUsers: 0,
      });
    } catch (error) {
      console.error("Error loading stats:", error);
    }
  };

  // Memoize callback function to prevent infinite re-renders
  const handleUsersStatsUpdate = useCallback((count) => {
    setStats((prev) => ({ ...prev, totalUsers: count }));
  }, []);

  return (
    <div className="admin-dashboard">
      {/* Header */}
      <header className="dashboard-header">
        <div className="header-content">
          <div className="user-info">
            <h1>Admin Dashboard</h1>
            <p>Welcome, {user.full_name}</p>
            {organizationInfo && (
              <p className="organization-info">
                Organization: {organizationInfo.name}
              </p>
            )}
          </div>
          <div className="header-actions">
            <button onClick={onLogout} className="btn btn-secondary">
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Stats Cards */}
      <div className="stats-section">
        <div className="stats-grid">
          <div className="stat-card">
            <h3>Total Users</h3>
            <p className="stat-number">{stats.totalUsers}</p>
          </div>
          <div className="stat-card">
            <h3>Organization</h3>
            <p className="stat-text">
              {organizationInfo?.name || "Loading..."}
            </p>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="dashboard-tabs">
        <button
          className={`tab-button ${activeTab === "users" ? "active" : ""}`}
          onClick={() => setActiveTab("users")}
        >
          👥 Users
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
          className={`tab-button ${activeTab === "profile" ? "active" : ""}`}
          onClick={() => setActiveTab("profile")}
        >
          👤 Profile
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
        {activeTab === "users" && (
          <UserManager
            adminId={user.id}
            onStatsUpdate={handleUsersStatsUpdate}
          />
        )}
        {activeTab === "chatbot" && <Chat />}
        {activeTab === "documents" && <Documents user={user} />}
        {activeTab === "profile" && (
          <AdminProfile admin={user} onUpdate={() => {}} />
        )}
        {activeTab === "settings" && <Settings />}
      </div>
    </div>
  );
};

export default AdminDashboard;
