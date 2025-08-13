import React, { useState, useEffect } from 'react';
import { getSystemStats, getAllUsers } from './api';

function Settings() {
  const [stats, setStats] = useState({
    total_documents: 0,
    total_chunks: 0,
    vector_db_status: 'unknown',
    ai_configured: false
  });
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadSystemData();
  }, []);

  const loadSystemData = async () => {
    setLoading(true);
    setError(null);
    try {
      // Load system stats
      const systemStats = await getSystemStats();
      setStats(systemStats);

      // Try to load users (admin only)
      try {
        const userList = await getAllUsers();
        setUsers(userList);
      } catch (userError) {
        console.log('User list not available (admin access required)');
      }
    } catch (error) {
      console.error('Failed to load system data:', error);
      setError('Failed to load system settings');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'connected':
      case 'healthy':
        return { bg: '#dcfce7', color: '#166534' };
      case 'error':
      case 'disconnected':
        return { bg: '#fef2f2', color: '#dc2626' };
      default:
        return { bg: '#fef3c7', color: '#92400e' };
    }
  };

  if (loading) {
    return (
      <div className="card">
        <h2>System Settings</h2>
        <div style={{ textAlign: 'center', padding: '40px' }}>Loading system information...</div>
      </div>
    );
  }

  return (
    <div className="card">
      <h2>System Settings & Status</h2>
      
      {error && (
        <div style={{ 
          background: 'rgba(239, 68, 68, 0.1)', 
          color: '#dc2626', 
          padding: '10px', 
          borderRadius: '6px', 
          marginBottom: '20px',
          fontSize: '14px'
        }}>
          {error}
        </div>
      )}
      
      {/* System Status */}
      <div style={{ marginBottom: '30px' }}>
        <h3>System Status</h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px', marginTop: '15px' }}>
          <div style={{ padding: '15px', backgroundColor: '#f9fafb', borderRadius: '8px' }}>
            <h4 style={{ margin: '0 0 10px 0', color: '#374151' }}>AI Service</h4>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div style={{
                ...getStatusColor(stats.ai_configured ? 'healthy' : 'error'),
                padding: '4px 8px',
                borderRadius: '4px',
                fontSize: '12px'
              }}>
                {stats.ai_configured ? '✅ Configured' : '❌ Not Configured'}
              </div>
            </div>
            <div style={{ fontSize: '12px', color: '#6b7280', marginTop: '5px' }}>
              Google Gemini API: {stats.ai_configured ? 'Active' : 'Missing API Key'}
            </div>
          </div>

          <div style={{ padding: '15px', backgroundColor: '#f9fafb', borderRadius: '8px' }}>
            <h4 style={{ margin: '0 0 10px 0', color: '#374151' }}>Vector Database</h4>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div style={{
                ...getStatusColor(stats.vector_db_status),
                padding: '4px 8px',
                borderRadius: '4px',
                fontSize: '12px'
              }}>
                {stats.vector_db_status || 'Unknown'}
              </div>
            </div>
            <div style={{ fontSize: '12px', color: '#6b7280', marginTop: '5px' }}>
              ChromaDB Local Instance
            </div>
          </div>
        </div>
      </div>

      {/* Document Statistics */}
      <div style={{ marginBottom: '30px' }}>
        <h3>Document Statistics</h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px', marginTop: '15px' }}>
          <div style={{ 
            padding: '20px', 
            backgroundColor: '#eff6ff', 
            borderRadius: '8px',
            textAlign: 'center'
          }}>
            <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#2563eb' }}>
              {stats.total_documents}
            </div>
            <div style={{ fontSize: '14px', color: '#1e40af', marginTop: '5px' }}>
              Total Documents
            </div>
          </div>

          <div style={{ 
            padding: '20px', 
            backgroundColor: '#f0fdf4', 
            borderRadius: '8px',
            textAlign: 'center'
          }}>
            <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#16a34a' }}>
              {stats.total_chunks}
            </div>
            <div style={{ fontSize: '14px', color: '#15803d', marginTop: '5px' }}>
              Text Chunks
            </div>
          </div>
        </div>
      </div>

      {/* AI Model Settings */}
      <div style={{ marginBottom: '30px' }}>
        <h3>AI Model Configuration</h3>
        <div style={{ padding: '15px', backgroundColor: '#f9fafb', borderRadius: '8px' }}>
          <div style={{ marginBottom: '15px' }}>
            <label style={{ display: 'block', marginBottom: '5px', fontWeight: '500' }}>
              Model: Google Gemini 1.5 Flash
            </label>
            <div style={{ fontSize: '14px', color: '#6b7280' }}>
              Fast and efficient model for RAG applications
            </div>
          </div>

          <div style={{ marginBottom: '15px' }}>
            <label style={{ display: 'block', marginBottom: '5px', fontWeight: '500' }}>
              Temperature: 0.1
            </label>
            <div style={{ fontSize: '14px', color: '#6b7280' }}>
              Low temperature for consistent, factual responses
            </div>
          </div>

          <div style={{ marginBottom: '15px' }}>
            <label style={{ display: 'block', marginBottom: '5px', fontWeight: '500' }}>
              Max Tokens: 500
            </label>
            <div style={{ fontSize: '14px', color: '#6b7280' }}>
              Maximum response length
            </div>
          </div>
        </div>
      </div>

      {/* User Management (Admin Only) */}
      {users.length > 0 && (
        <div style={{ marginBottom: '30px' }}>
          <h3>User Management</h3>
          <div style={{ maxHeight: '200px', overflowY: 'auto' }}>
            {users.map((user) => (
              <div key={user.id} style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '12px',
                backgroundColor: '#f9fafb',
                borderRadius: '6px',
                marginBottom: '8px'
              }}>
                <div>
                  <div style={{ fontWeight: '500', color: '#374151' }}>
                    {user.username}
                  </div>
                  <div style={{ fontSize: '14px', color: '#6b7280' }}>
                    {user.email} • Role: {user.role}
                  </div>
                </div>
                <div style={{
                  padding: '4px 8px',
                  backgroundColor: user.is_active ? '#dcfce7' : '#fef2f2',
                  color: user.is_active ? '#166534' : '#dc2626',
                  borderRadius: '4px',
                  fontSize: '12px'
                }}>
                  {user.is_active ? 'Active' : 'Inactive'}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Refresh Button */}
      <div style={{ textAlign: 'center' }}>
        <button 
          onClick={loadSystemData} 
          className="button"
          disabled={loading}
        >
          {loading ? 'Refreshing...' : 'Refresh Status'}
        </button>
      </div>

      <div style={{ 
        fontSize: '12px', 
        color: '#6b7280', 
        textAlign: 'center',
        marginTop: '20px',
        padding: '15px',
        backgroundColor: '#f9fafb',
        borderRadius: '6px'
      }}>
        <div style={{ marginBottom: '8px' }}>
          <strong>API Endpoint:</strong> http://localhost:8001/api
        </div>
        <div style={{ marginBottom: '8px' }}>
          <strong>Frontend:</strong> http://localhost:3000
        </div>
        <div>
          <strong>Documentation:</strong> <a href="http://localhost:8001/docs" target="_blank" rel="noopener noreferrer">API Docs</a>
        </div>
      </div>
    </div>
  );
}

export default Settings;
