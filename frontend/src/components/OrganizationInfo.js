import React, { useState, useEffect } from "react";
import { getOrganization } from "../api";
import "./OrganizationInfo.css";

const OrganizationInfo = ({ organizationId }) => {
  const [organization, setOrganization] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (organizationId) {
      loadOrganization();
    }
  }, [organizationId]);

  const loadOrganization = async () => {
    try {
      setLoading(true);
      const data = await getOrganization(organizationId);
      setOrganization(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="organization-info">
        <div className="loading">Loading organization information...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="organization-info">
        <div className="error-message">Error loading organization: {error}</div>
      </div>
    );
  }

  if (!organization) {
    return (
      <div className="organization-info">
        <div className="empty-state">
          <p>No organization information available.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="organization-info">
      <h2>Organization Information</h2>

      <div className="org-card">
        <div className="org-header">
          <h3>{organization.name}</h3>
          <span className="org-id">ID: {organization.organization_id}</span>
        </div>

        <div className="org-details">
          <div className="org-field">
            <label>Organization Name:</label>
            <span>{organization.name}</span>
          </div>
          <div className="org-field">
            <label>Organization ID:</label>
            <span>{organization.organization_id}</span>
          </div>
          <div className="org-field">
            <label>Created:</label>
            <span>
              {new Date(organization.created_at).toLocaleDateString()}
            </span>
          </div>
        </div>

        <div className="org-stats">
          <div className="stat-item">
            <h4>Organization Details</h4>
            <p>
              This organization was created on{" "}
              {new Date(organization.created_at).toLocaleDateString()}.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OrganizationInfo;
