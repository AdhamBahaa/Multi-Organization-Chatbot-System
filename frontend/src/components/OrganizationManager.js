import React, { useState, useEffect } from "react";
import {
  createOrganization,
  getOrganizations,
  updateOrganization,
  deleteOrganization,
} from "../api";
import "./OrganizationManager.css";

const OrganizationManager = ({ onStatsUpdate }) => {
  const [organizations, setOrganizations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingOrg, setEditingOrg] = useState(null);
  const [formData, setFormData] = useState({ name: "" });

  useEffect(() => {
    loadOrganizations();
  }, []);

  useEffect(() => {
    onStatsUpdate(organizations.length);
  }, [organizations.length, onStatsUpdate]);

  const loadOrganizations = async () => {
    try {
      setLoading(true);
      const data = await getOrganizations();
      setOrganizations(data);
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
      await createOrganization(formData.name);
      setFormData({ name: "" });
      setShowCreateForm(false);
      await loadOrganizations();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleUpdate = async (e) => {
    e.preventDefault();
    try {
      await updateOrganization(editingOrg.organization_id, formData.name);
      setFormData({ name: "" });
      setEditingOrg(null);
      await loadOrganizations();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDelete = async (orgId, orgName) => {
    if (
      window.confirm(
        `Are you sure you want to delete "${orgName}"? This will also delete all admins and users in this organization.`
      )
    ) {
      try {
        await deleteOrganization(orgId);
        await loadOrganizations();
      } catch (err) {
        setError(err.message);
      }
    }
  };

  const startEdit = (org) => {
    setEditingOrg(org);
    setFormData({ name: org.name });
  };

  const cancelEdit = () => {
    setEditingOrg(null);
    setFormData({ name: "" });
  };

  if (loading) {
    return <div className="loading">Loading organizations...</div>;
  }

  return (
    <div className="organization-manager">
      <div className="manager-header">
        <h2>Organizations</h2>
        <button
          className="btn btn-primary"
          onClick={() => setShowCreateForm(true)}
        >
          Create Organization
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}

      {/* Create Form */}
      {showCreateForm && (
        <div className="form-overlay">
          <div className="form-modal">
            <h3>Create Organization</h3>
            <form onSubmit={handleCreate}>
              <div className="form-group">
                <label>Organization Name:</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ name: e.target.value })}
                  required
                  placeholder="Enter organization name"
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
      {editingOrg && (
        <div className="form-overlay">
          <div className="form-modal">
            <h3>Edit Organization</h3>
            <form onSubmit={handleUpdate}>
              <div className="form-group">
                <label>Organization Name:</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ name: e.target.value })}
                  required
                  placeholder="Enter organization name"
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

      {/* Organizations List */}
      <div className="organizations-list">
        {organizations.length === 0 ? (
          <div className="empty-state">
            <p>No organizations found. Create your first organization!</p>
          </div>
        ) : (
          organizations.map((org) => (
            <div key={org.organization_id} className="organization-card">
              <div className="org-info">
                <h3>{org.name}</h3>
                <p>ID: {org.organization_id}</p>
                <p>Created: {new Date(org.created_at).toLocaleDateString()}</p>
              </div>
              <div className="org-actions">
                <button
                  className="btn btn-secondary"
                  onClick={() => startEdit(org)}
                >
                  Edit
                </button>
                <button
                  className="btn btn-danger"
                  onClick={() => handleDelete(org.organization_id, org.name)}
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

export default OrganizationManager;
