import React, { useState } from 'react';
import { login } from './api';

function Login({ onLogin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      const result = await login(username, password);
      localStorage.setItem('token', result.token);
      localStorage.setItem('user', JSON.stringify(result.user));
      onLogin(result.user);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fillDemo = (type) => {
    if (type === 'admin') {
      setUsername('admin');
      setPassword('admin123');
    } else {
      setUsername('user');
      setPassword('user123');
    }
  };

  return (
    <div className="container">
      <div className="header">
        <h1>RAG Chatbot</h1>
        <p>Simple Document-Based AI Assistant</p>
      </div>
      
      <div className="card" style={{maxWidth: '400px', margin: '0 auto'}}>
        <h2>Sign In</h2>
        
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Username</label>
            <input
              type="text"
              className="input"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>
          
          <div className="form-group">
            <label>Password</label>
            <input
              type="password"
              className="input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          
          {error && <div className="error">{error}</div>}
          
          <button type="submit" className="button" disabled={loading}>
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>
        
        <div style={{marginTop: '20px', padding: '15px', background: '#f9fafb', borderRadius: '6px'}}>
          <p style={{margin: '0 0 10px 0', fontSize: '14px', color: '#6b7280'}}>Demo Accounts:</p>
          <div style={{display: 'flex', gap: '10px'}}>
            <button 
              type="button" 
              className="button" 
              style={{background: '#10b981', fontSize: '12px', padding: '8px 12px'}}
              onClick={() => fillDemo('admin')}
            >
              Admin Demo
            </button>
            <button 
              type="button" 
              className="button" 
              style={{background: '#8b5cf6', fontSize: '12px', padding: '8px 12px'}}
              onClick={() => fillDemo('user')}
            >
              User Demo
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Login;
