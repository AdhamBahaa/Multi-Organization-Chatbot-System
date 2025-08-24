import React, { useState, useEffect } from "react";
import { createUser, getUsers, updateUser, deleteUser } from "../api";
import "./UserManager.css";

const UserManager = ({ adminId, onStatsUpdate }) => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [createFormError, setCreateFormError] = useState("");
  const [editFormError, setEditFormError] = useState("");
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [formData, setFormData] = useState({
    full_name: "",
    email: "",
    role: "Member",
  });

  useEffect(() => {
    loadUsers();
  }, []);

  useEffect(() => {
    onStatsUpdate(users.length);
  }, [users.length, onStatsUpdate]);

  const loadUsers = async () => {
    try {
      setLoading(true);
      const data = await getUsers();
      setUsers(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    setCreateFormError("");
    try {
      await createUser(
        adminId,
        formData.full_name,
        formData.email,
        formData.role
      );
      setFormData({ full_name: "", email: "", role: "Member" });
      setShowCreateForm(false);
      await loadUsers();
    } catch (err) {
      setCreateFormError(err.message);
    }
  };

  const handleUpdate = async (e) => {
    e.preventDefault();
    setEditFormError("");
    try {
      await updateUser(
        editingUser.user_id,
        formData.full_name,
        formData.email,
        formData.role
      );
      setFormData({ full_name: "", email: "", role: "Member" });
      setEditingUser(null);
      await loadUsers();
    } catch (err) {
      setEditFormError(err.message);
    }
  };

  const handleDelete = async (userId, userName) => {
    if (window.confirm(`Are you sure you want to delete "${userName}"?`)) {
      try {
        await deleteUser(userId);
        await loadUsers();
      } catch (err) {
        setError(err.message);
      }
    }
  };

  const startEdit = (user) => {
    setEditingUser(user);
    setFormData({
      full_name: user.full_name,
      email: user.email,
      role: user.role,
    });
  };

  const cancelEdit = () => {
    setEditingUser(null);
    setEditFormError("");
    setFormData({ full_name: "", email: "", role: "Member" });
  };

  if (loading) {
    return <div className="loading">Loading users...</div>;
  }

  return (
    <div className="user-manager">
      <div className="manager-header">
        <h2>Users</h2>
        <button
          className="btn btn-primary"
          onClick={() => setShowCreateForm(true)}
        >
          Create User
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}

      {/* Create Form */}
      {showCreateForm && (
        <div className="form-overlay">
          <div className="form-modal">
            <h3>Create User</h3>
            <form onSubmit={handleCreate}>
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
              <div className="form-group">
                <label>Role:</label>
                <input
                  type="text"
                  value={formData.role}
                  onChange={(e) =>
                    setFormData({ ...formData, role: e.target.value })
                  }
                  required
                  placeholder="Enter role (e.g., Member, Manager, etc.)"
                />
              </div>
              {createFormError && (
                <div className="error-message" style={{ marginBottom: "1rem" }}>
                  {createFormError}
                </div>
              )}
              <div className="form-actions">
                <button type="submit" className="btn btn-primary">
                  Create
                </button>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => {
                    setShowCreateForm(false);
                    setCreateFormError("");
                  }}
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Form */}
      {editingUser && (
        <div className="form-overlay">
          <div className="form-modal">
            <h3>Edit User</h3>
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
              <div className="form-group">
                <label>Role:</label>
                <input
                  type="text"
                  value={formData.role}
                  onChange={(e) =>
                    setFormData({ ...formData, role: e.target.value })
                  }
                  required
                  placeholder="Enter role"
                />
              </div>
              {editFormError && (
                <div className="error-message" style={{ marginBottom: "1rem" }}>
                  {editFormError}
                </div>
              )}
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

      {/* Users List */}
      <div className="users-list">
        {users.length === 0 ? (
          <div className="empty-state">
            <p>No users found. Create your first user!</p>
          </div>
        ) : (
          users.map((user) => (
            <div key={user.user_id} className="user-card">
              <div className="user-info">
                <h3>{user.full_name}</h3>
                <p>Email: {user.email}</p>
                <p>ID: {user.user_id}</p>
                <p>Role: {user.role}</p>
                <p>
                  Status:{" "}
                  <span
                    style={{
                      color: user.is_activated ? "#166534" : "#dc2626",
                      fontWeight: "bold",
                    }}
                  >
                    {user.is_activated ? "✅ Activated" : "❌ Not Activated"}
                  </span>
                </p>
                <p>Created: {new Date(user.created_at).toLocaleDateString()}</p>
                {user.setup_link && !user.is_activated && (
                  <div className="setup-link-section">
                    <p className="setup-notice">
                      <strong>⚠️ New User - Password Setup Required</strong>
                    </p>
                    <p className="email-status">
                      <strong>
                        📧 Setup email sent automatically to: {user.email}
                      </strong>
                    </p>
                    <p className="setup-link">
                      Manual Setup Link:{" "}
                      <a
                        href={`${window.location.origin}${user.setup_link}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="setup-url"
                      >
                        {window.location.origin}
                        {user.setup_link}
                      </a>
                    </p>
                    <button
                      className="btn btn-copy"
                      onClick={() => {
                        navigator.clipboard.writeText(
                          `${window.location.origin}${user.setup_link}`
                        );
                        alert("Setup link copied to clipboard!");
                      }}
                    >
                      Copy Link
                    </button>
                  </div>
                )}
              </div>
              <div className="user-actions">
                <button
                  className="btn btn-secondary"
                  onClick={() => startEdit(user)}
                >
                  Edit
                </button>
                <button
                  className="btn btn-danger"
                  onClick={() => handleDelete(user.user_id, user.full_name)}
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

export default UserManager;
