import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import SuperAdminDashboard from "./dashboards/SuperAdminDashboard";
import AdminDashboard from "./dashboards/AdminDashboard";
import UserDashboard from "./dashboards/UserDashboard";
import { logout } from "./api";
import "./Dashboard.css";

const Dashboard = () => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const userData = localStorage.getItem("user");
    if (!userData) {
      navigate("/login");
      return;
    }

    try {
      const userObj = JSON.parse(userData);
      setUser(userObj);
    } catch (error) {
      console.error("Error parsing user data:", error);
      navigate("/login");
    } finally {
      setLoading(false);
    }
  }, [navigate]);

  const handleLogout = async () => {
    try {
      await logout();
    } catch (error) {
      console.error("Logout error:", error);
    } finally {
      // Force page reload to ensure clean state
      window.location.href = "/login";
    }
  };

  if (loading) {
    return (
      <div className="dashboard-loading">
        <div className="loading-spinner"></div>
        <p>Loading dashboard...</p>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  const renderDashboard = () => {
    switch (user.role) {
      case "super_admin":
        return <SuperAdminDashboard user={user} onLogout={handleLogout} />;
      case "admin":
        return <AdminDashboard user={user} onLogout={handleLogout} />;
      case "user":
        return <UserDashboard user={user} onLogout={handleLogout} />;
      default:
        return (
          <div className="dashboard-error">
            <h2>Unknown Role</h2>
            <p>Your role ({user.role}) is not recognized.</p>
            <button onClick={handleLogout} className="btn btn-primary">
              Logout
            </button>
          </div>
        );
    }
  };

  return <div className="dashboard-container">{renderDashboard()}</div>;
};

export default Dashboard;
