import React, { useState, useEffect, useCallback } from "react";
import OrganizationManager from "../components/OrganizationManager";
import AdminManager from "../components/AdminManager";
import "./SuperAdminDashboard.css";

const SuperAdminDashboard = ({ user, onLogout }) => {
  const [activeTab, setActiveTab] = useState("organizations");
  const [stats, setStats] = useState({
    totalOrganizations: 0,
    totalAdmins: 0,
  });

  useEffect(() => {
    // Load initial stats
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      // You can add API calls here to get real stats
      setStats({
        totalOrganizations: 0, // Will be updated by components
        totalAdmins: 0, // Will be updated by components
      });
    } catch (error) {
      console.error("Error loading stats:", error);
    }
  };

  // Memoize callback functions to prevent infinite re-renders
  const handleOrganizationsStatsUpdate = useCallback((count) => {
    setStats((prev) => ({ ...prev, totalOrganizations: count }));
  }, []);

  const handleAdminsStatsUpdate = useCallback((count) => {
    setStats((prev) => ({ ...prev, totalAdmins: count }));
  }, []);

  return (
    <div className="super-admin-dashboard">
      {/* Header */}
      <header className="dashboard-header">
        <div className="header-content">
          <div className="user-info">
            <h1>Super Admin Dashboard</h1>
            <p>Welcome, {user.full_name}</p>
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
            <h3>Total Organizations</h3>
            <p className="stat-number">{stats.totalOrganizations}</p>
          </div>
          <div className="stat-card">
            <h3>Total Admins</h3>
            <p className="stat-number">{stats.totalAdmins}</p>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="dashboard-tabs">
        <button
          className={`tab-button ${
            activeTab === "organizations" ? "active" : ""
          }`}
          onClick={() => setActiveTab("organizations")}
        >
          🏢 Organizations
        </button>
        <button
          className={`tab-button ${activeTab === "admins" ? "active" : ""}`}
          onClick={() => setActiveTab("admins")}
        >
          👥 Admins
        </button>
      </div>

      {/* Content Area */}
      <div className="dashboard-content">
        {activeTab === "organizations" && (
          <OrganizationManager onStatsUpdate={handleOrganizationsStatsUpdate} />
        )}
        {activeTab === "admins" && (
          <AdminManager onStatsUpdate={handleAdminsStatsUpdate} />
        )}
      </div>
    </div>
  );
};

export default SuperAdminDashboard;
