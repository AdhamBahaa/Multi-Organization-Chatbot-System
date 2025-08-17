import axios from "axios";

const API_BASE = "http://localhost:8002/api";

// Create axios instance
const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

// Add auth token to requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token");
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
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      window.location.reload();
    }
    return Promise.reject(error);
  }
);

// Auth API
export const login = async (email, password) => {
  try {
    const response = await api.post("/login", { email, password });
    const data = response.data;

    // Store token and user info
    localStorage.setItem("token", data.access_token);
    localStorage.setItem(
      "user",
      JSON.stringify({
        id: data.user_id,
        email: data.email,
        role: data.role,
        organization_id: data.organization_id,
        admin_id: data.admin_id,
      })
    );

    return {
      token: data.access_token,
      user: {
        id: data.user_id,
        email: data.email,
        role: data.role,
        organization_id: data.organization_id,
        admin_id: data.admin_id,
      },
    };
  } catch (error) {
    console.error(
      "Login error:",
      error.response?.data?.detail || error.message
    );
    throw new Error(error.response?.data?.detail || "Login failed");
  }
};

export const getCurrentUser = async () => {
  try {
    const response = await api.get("/profile");
    return response.data;
  } catch (error) {
    throw new Error("Failed to get user info");
  }
};

// Super Admin API
export const createOrganization = async (name) => {
  try {
    const response = await api.post("/organizations", { name });
    return response.data;
  } catch (error) {
    console.error(
      "Create organization error:",
      error.response?.data?.detail || error.message
    );
    throw new Error(
      error.response?.data?.detail || "Failed to create organization"
    );
  }
};

export const getOrganizations = async () => {
  try {
    const response = await api.get("/organizations");
    return response.data;
  } catch (error) {
    console.error(
      "Get organizations error:",
      error.response?.data?.detail || error.message
    );
    throw new Error(
      error.response?.data?.detail || "Failed to get organizations"
    );
  }
};

export const getOrganization = async (organizationId) => {
  try {
    const response = await api.get(`/organizations/${organizationId}`);
    return response.data;
  } catch (error) {
    console.error(
      "Get organization error:",
      error.response?.data?.detail || error.message
    );
    throw new Error(
      error.response?.data?.detail || "Failed to get organization"
    );
  }
};

export const updateOrganization = async (organizationId, name) => {
  try {
    const response = await api.put(`/organizations/${organizationId}`, {
      name,
    });
    return response.data;
  } catch (error) {
    console.error(
      "Update organization error:",
      error.response?.data?.detail || error.message
    );
    throw new Error(
      error.response?.data?.detail || "Failed to update organization"
    );
  }
};

export const deleteOrganization = async (organizationId) => {
  try {
    const response = await api.delete(`/organizations/${organizationId}`);
    return response.data;
  } catch (error) {
    console.error(
      "Delete organization error:",
      error.response?.data?.detail || error.message
    );
    throw new Error(
      error.response?.data?.detail || "Failed to delete organization"
    );
  }
};

export const createAdmin = async (organizationId, fullName, email) => {
  try {
    const response = await api.post("/admins", {
      organization_id: organizationId,
      full_name: fullName,
      email: email,
    });
    return response.data;
  } catch (error) {
    console.error(
      "Create admin error:",
      error.response?.data?.detail || error.message
    );
    throw new Error(error.response?.data?.detail || "Failed to create admin");
  }
};

export const getAdmins = async () => {
  try {
    const response = await api.get("/admins");
    return response.data;
  } catch (error) {
    console.error(
      "Get admins error:",
      error.response?.data?.detail || error.message
    );
    throw new Error(error.response?.data?.detail || "Failed to get admins");
  }
};

export const getAdmin = async (adminId) => {
  try {
    const response = await api.get(`/admins/${adminId}`);
    return response.data;
  } catch (error) {
    console.error(
      "Get admin error:",
      error.response?.data?.detail || error.message
    );
    throw new Error(error.response?.data?.detail || "Failed to get admin");
  }
};

export const updateAdmin = async (adminId, fullName, email) => {
  try {
    const response = await api.put(`/admins/${adminId}`, {
      full_name: fullName,
      email: email,
    });
    return response.data;
  } catch (error) {
    console.error(
      "Update admin error:",
      error.response?.data?.detail || error.message
    );
    throw new Error(error.response?.data?.detail || "Failed to update admin");
  }
};

export const deleteAdmin = async (adminId) => {
  try {
    const response = await api.delete(`/admins/${adminId}`);
    return response.data;
  } catch (error) {
    console.error(
      "Delete admin error:",
      error.response?.data?.detail || error.message
    );
    throw new Error(error.response?.data?.detail || "Failed to delete admin");
  }
};

// Admin API
export const createUser = async (adminId, fullName, email, role) => {
  try {
    const response = await api.post("/users", {
      admin_id: adminId,
      full_name: fullName,
      email: email,
      role: role,
    });
    return response.data;
  } catch (error) {
    console.error(
      "Create user error:",
      error.response?.data?.detail || error.message
    );
    throw new Error(error.response?.data?.detail || "Failed to create user");
  }
};

export const getUsers = async () => {
  try {
    const response = await api.get("/users");
    return response.data;
  } catch (error) {
    console.error(
      "Get users error:",
      error.response?.data?.detail || error.message
    );
    throw new Error(error.response?.data?.detail || "Failed to get users");
  }
};

export const getUser = async (userId) => {
  try {
    const response = await api.get(`/users/${userId}`);
    return response.data;
  } catch (error) {
    console.error(
      "Get user error:",
      error.response?.data?.detail || error.message
    );
    throw new Error(error.response?.data?.detail || "Failed to get user");
  }
};

export const updateUser = async (userId, fullName, email, role) => {
  try {
    const response = await api.put(`/users/${userId}`, {
      full_name: fullName,
      email: email,
      role: role,
    });
    return response.data;
  } catch (error) {
    console.error(
      "Update user error:",
      error.response?.data?.detail || error.message
    );
    throw new Error(error.response?.data?.detail || "Failed to update user");
  }
};

export const deleteUser = async (userId) => {
  try {
    const response = await api.delete(`/users/${userId}`);
    return response.data;
  } catch (error) {
    console.error(
      "Delete user error:",
      error.response?.data?.detail || error.message
    );
    throw new Error(error.response?.data?.detail || "Failed to delete user");
  }
};

// Chat API
export const sendMessage = async (message, sessionId = null) => {
  try {
    const response = await api.post("/chat", {
      message,
      session_id: sessionId,
    });
    return response.data;
  } catch (error) {
    console.error("Chat error:", error.response?.data?.detail || error.message);
    throw new Error(error.response?.data?.detail || "Failed to send message");
  }
};

export const getChatSessions = async () => {
  try {
    const response = await api.get("/sessions");
    return response.data;
  } catch (error) {
    console.error("Sessions error:", error);
    return [];
  }
};

export const getSessionMessages = async (sessionId) => {
  try {
    const response = await api.get(`/sessions/${sessionId}/messages`);
    return response.data;
  } catch (error) {
    console.error("Messages error:", error);
    return [];
  }
};

// Document API
export const uploadDocument = async (file) => {
  try {
    const formData = new FormData();
    formData.append("file", file);

    const response = await api.post("/documents/upload", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
      timeout: 60000, // 60 seconds for file upload
    });
    return response.data;
  } catch (error) {
    console.error(
      "Upload error:",
      error.response?.data?.detail || error.message
    );
    throw new Error(error.response?.data?.detail || "Upload failed");
  }
};

export const getDocuments = async () => {
  try {
    const response = await api.get("/documents");
    return response.data;
  } catch (error) {
    console.error("Documents error:", error);
    return [];
  }
};

export const deleteDocument = async (documentId) => {
  try {
    const response = await api.delete(`/documents/${documentId}`);
    return response.data;
  } catch (error) {
    console.error(
      "Delete error:",
      error.response?.data?.detail || error.message
    );
    throw new Error(error.response?.data?.detail || "Delete failed");
  }
};

// Admin API
export const getSystemStats = async () => {
  try {
    const response = await api.get("/system/stats");
    return response.data;
  } catch (error) {
    console.error("Stats error:", error);
    return {
      total_documents: 0,
      total_chunks: 0,
      vector_db_status: "unknown",
      ai_configured: false,
    };
  }
};

export default api;
