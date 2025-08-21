import React, { useState, useEffect } from "react";
import {
  createAdmin,
  getAdmins,
  updateAdmin,
  deleteAdmin,
  getOrganizations,
} from "../api";
import "./AdminManager.css";

const AdminManager = ({ onStatsUpdate }) => {
  const [admins, setAdmins] = useState([]);
  const [organizations, setOrganizations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingAdmin, setEditingAdmin] = useState(null);
  const [formData, setFormData] = useState({
    organization_id: "",
    full_name: "",
    email: "",
  });

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    onStatsUpdate(admins.length);
  }, [admins.length, onStatsUpdate]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [adminsData, orgsData] = await Promise.all([
        getAdmins(),
        getOrganizations(),
      ]);
      setAdmins(adminsData);
      setOrganizations(orgsData);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      await createAdmin(
        parseInt(formData.organization_id),
        formData.full_name,
        formData.email
      );
      setFormData({ organization_id: "", full_name: "", email: "" });
      setShowCreateForm(false);
      await loadData();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleUpdate = async (e) => {
    e.preventDefault();
    try {
      await updateAdmin(
        editingAdmin.admin_id,
        formData.full_name,
        formData.email
      );
      setFormData({ organization_id: "", full_name: "", email: "" });
      setEditingAdmin(null);
      await loadData();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDelete = async (adminId, adminName) => {
    if (
      window.confirm(
        `Are you sure you want to delete "${adminName}"? This will also delete all users under this admin.`
      )
    ) {
      try {
        await deleteAdmin(adminId);
        await loadData();
      } catch (err) {
        setError(err.message);
      }
    }
  };

  const startEdit = (admin) => {
    setEditingAdmin(admin);
    setFormData({
      organization_id: admin.organization_id.toString(),
      full_name: admin.full_name,
      email: admin.email,
    });
  };

  const cancelEdit = () => {
    setEditingAdmin(null);
    setFormData({ organization_id: "", full_name: "", email: "" });
  };

  const getOrganizationName = (orgId) => {
    const org = organizations.find((o) => o.organization_id === orgId);
    return org ? org.name : "Unknown Organization";
  };

  if (loading) {
    return <div className="loading">Loading admins...</div>;
  }

  return (
    <div className="admin-manager">
      <div className="manager-header">
        <h2>Admins</h2>
        <button
          className="btn btn-primary"
          onClick={() => setShowCreateForm(true)}
        >
          Create Admin
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}

      {/* Create Form */}
      {showCreateForm && (
        <div className="form-overlay">
          <div className="form-modal">
            <h3>Create Admin</h3>
            <form onSubmit={handleCreate}>
              <div className="form-group">
                <label>Organization:</label>
                <select
                  value={formData.organization_id}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      organization_id: e.target.value,
                    })
                  }
                  required
                >
                  <option value="">Select Organization</option>
                  {organizations.map((org) => (
                    <option
                      key={org.organization_id}
                      value={org.organization_id}
                    >
                      {org.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>Full Name:</label>
                <input
                  type="text"
                  value={formData.full_name}
                  onChange={(e) =>
                    setFormData({ ...formData, full_name: e.target.value })
                  }
                  required
                  placeholder="Enter full name"
                />
              </div>
              <div className="form-group">
                <label>Email:</label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) =>
                    setFormData({ ...formData, email: e.target.value })
                  }
                  required
                  placeholder="Enter email"
                />
              </div>
              <div className="form-actions">
                <button type="submit" className="btn btn-primary">
                  Create
                </button>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setShowCreateForm(false)}
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Form */}
      {editingAdmin && (
        <div className="form-overlay">
          <div className="form-modal">
            <h3>Edit Admin</h3>
            <form onSubmit={handleUpdate}>
              <div className="form-group">
                <label>Full Name:</label>
                <input
                  type="text"
                  value={formData.full_name}
                  onChange={(e) =>
                    setFormData({ ...formData, full_name: e.target.value })
                  }
                  required
                  placeholder="Enter full name"
                />
              </div>
              <div className="form-group">
                <label>Email:</label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) =>
                    setFormData({ ...formData, email: e.target.value })
                  }
                  required
                  placeholder="Enter email"
                />
              </div>
              <div className="form-actions">
                <button type="submit" className="btn btn-primary">
                  Update
                </button>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={cancelEdit}
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Admins List */}
      <div className="admins-list">
        {admins.length === 0 ? (
          <div className="empty-state">
            <p>No admins found. Create your first admin!</p>
          </div>
        ) : (
          admins.map((admin) => (
            <div key={admin.admin_id} className="admin-card">
              <div className="admin-info">
                <h3>{admin.full_name}</h3>
                <p>Email: {admin.email}</p>
                <p>ID: {admin.admin_id}</p>
                <p>
                  Organization: {getOrganizationName(admin.organization_id)}
                </p>
                <p>
                  Created: {new Date(admin.created_at).toLocaleDateString()}
                </p>
                <p>
                  Status:{" "}
                  <span
                    style={{
                      color: admin.is_activated ? "#166534" : "#dc2626",
                      fontWeight: "bold",
                    }}
                  >
                    {admin.is_activated ? "✅ Activated" : "❌ Not Activated"}
                  </span>
                </p>
                {admin.setup_link && !admin.is_activated && (
                  <div className="setup-link-section">
                    <p className="setup-notice">
                      <strong>⚠️ New Admin - Password Setup Required</strong>
                    </p>
                    <p className="email-status">
                      <strong>
                        📧 Setup email sent automatically to: {admin.email}
                      </strong>
                    </p>
                    <p className="setup-link">
                      Manual Setup Link:{" "}
                      <a
                        href={`${window.location.origin}${admin.setup_link}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="setup-url"
                      >
                        {window.location.origin}
                        {admin.setup_link}
                      </a>
                    </p>
                    <button
                      className="btn btn-copy"
                      onClick={() => {
                        navigator.clipboard.writeText(
                          `${window.location.origin}${admin.setup_link}`
                        );
                        alert("Setup link copied to clipboard!");
                      }}
                    >
                      Copy Link
                    </button>
                  </div>
                )}
              </div>
              <div className="admin-actions">
                <button
                  className="btn btn-secondary"
                  onClick={() => startEdit(admin)}
                >
                  Edit
                </button>
                <button
                  className="btn btn-danger"
                  onClick={() => handleDelete(admin.admin_id, admin.full_name)}
                >
                  Delete
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default AdminManager;
