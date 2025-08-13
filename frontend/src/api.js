import axios from 'axios';

const API_BASE = 'http://localhost:8002/api';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  }
});

// Add auth token to requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.reload();
    }
    return Promise.reject(error);
  }
);

// Auth API
export const login = async (username, password) => {
  try {
    const response = await api.post('/login', { username, password });
    const data = response.data;
    
    // Store token and user info
    localStorage.setItem('token', data.access_token);
    localStorage.setItem('user', JSON.stringify({
      id: data.user_id,
      username: data.username,
      role: data.role
    }));
    
    return {
      token: data.access_token,
      user: {
        id: data.user_id,
        username: data.username,
        role: data.role
      }
    };
  } catch (error) {
    console.error('Login error:', error.response?.data?.detail || error.message);
    throw new Error(error.response?.data?.detail || 'Login failed');
  }
};

export const getCurrentUser = async () => {
  try {
    const response = await api.get('/me');
    return response.data;
  } catch (error) {
    throw new Error('Failed to get user info');
  }
};

// Chat API
export const sendMessage = async (message, sessionId = null) => {
  try {
    const response = await api.post('/chat', { 
      message, 
      session_id: sessionId 
    });
    return response.data;
  } catch (error) {
    console.error('Chat error:', error.response?.data?.detail || error.message);
    throw new Error(error.response?.data?.detail || 'Failed to send message');
  }
};

export const getChatSessions = async () => {
  try {
    const response = await api.get('/sessions');
    return response.data;
  } catch (error) {
    console.error('Sessions error:', error);
    return [];
  }
};

export const getSessionMessages = async (sessionId) => {
  try {
    const response = await api.get(`/sessions/${sessionId}/messages`);
    return response.data;
  } catch (error) {
    console.error('Messages error:', error);
    return [];
  }
};

// Document API
export const uploadDocument = async (file) => {
  try {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 60000, // 60 seconds for file upload
    });
    return response.data;
  } catch (error) {
    console.error('Upload error:', error.response?.data?.detail || error.message);
    throw new Error(error.response?.data?.detail || 'Upload failed');
  }
};

export const getDocuments = async () => {
  try {
    const response = await api.get('/documents');
    return response.data;
  } catch (error) {
    console.error('Documents error:', error);
    return [];
  }
};

export const deleteDocument = async (documentId) => {
  try {
    const response = await api.delete(`/documents/${documentId}`);
    return response.data;
  } catch (error) {
    console.error('Delete error:', error.response?.data?.detail || error.message);
    throw new Error(error.response?.data?.detail || 'Delete failed');
  }
};

// Admin API
export const getSystemStats = async () => {
  try {
    const response = await api.get('/system/stats');
    return response.data;
  } catch (error) {
    console.error('Stats error:', error);
    return {
      total_documents: 0,
      total_chunks: 0,
      vector_db_status: 'unknown',
      ai_configured: false
    };
  }
};

export const getAllUsers = async () => {
  try {
    const response = await api.get('/admin/users');
    return response.data;
  } catch (error) {
    console.error('Users error:', error);
    return [];
  }
};

export default api;
