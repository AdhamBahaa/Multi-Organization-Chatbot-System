import axios from "axios";
import { API_BASE } from "./config";

// Create axios instance
const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

// Helper function to extract error message from different error response formats
const extractErrorMessage = (error, defaultMessage = "Request failed") => {
  if (error.response?.data) {
    const errorData = error.response.data;

    // Handle FastAPI validation errors (422 status code)
    // FastAPI format: { detail: [{ loc: [...], msg: "...", type: "..." }] }
    if (
      error.response.status === 422 &&
      errorData.detail &&
      Array.isArray(errorData.detail)
    ) {
      return errorData.detail
        .map((err) => {
          // FastAPI validation error structure: {loc: [...], msg: "...", type: "..."}
          if (err.msg) {
            return err.msg; // Just return the message, skip location for cleaner output
          }
          return err.message || err.detail || "Validation error";
        })
        .join(", ");
    }

    // Handle standard error format with detail as string
    else if (errorData.detail && typeof errorData.detail === "string") {
      return errorData.detail;
    }

    // Handle error message format
    else if (errorData.message && typeof errorData.message === "string") {
      return errorData.message;
    }

    // Handle direct array format (fallback)
    else if (Array.isArray(errorData)) {
      return errorData
        .map((err) => {
          if (typeof err === "string") return err;
          return err.msg || err.message || err.detail || "Validation error";
        })
        .join(", ");
    }

    // Handle detail as array (fallback)
    else if (errorData.detail && Array.isArray(errorData.detail)) {
      return errorData.detail
        .map((err) => {
          if (typeof err === "string") return err;
          return err.msg || err.message || err.detail || "Validation error";
        })
        .join(", ");
    }

    // Fallback: try to stringify the entire error data
    try {
      if (typeof errorData === "object") {
        return JSON.stringify(errorData);
      }
      return String(errorData);
    } catch (e) {
      // Silent fallback if stringify fails
    }
  }

  return error.message || defaultMessage;
};

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
    // Don't auto-logout on refresh-session endpoint failures
    // This prevents the vicious cycle of refresh failing -> logout -> refresh failing
    if (error.config?.url?.includes("/auth/refresh-session")) {
      return Promise.reject(error);
    }

    if (error.response?.status === 401 || error.response?.status === 403) {
      // Remove session refresh listeners before logout
      removeSessionRefreshListeners();

      localStorage.removeItem("token");
      localStorage.removeItem("user");
      // Store expiration reason for login page
      localStorage.setItem("logoutReason", "session_expired");
      window.location.reload();
    }
    return Promise.reject(error);
  }
);

// Function to check token expiry and logout if expired
export const checkTokenExpiry = () => {
  const token = localStorage.getItem("token");
  if (!token) return;

  try {
    // Decode JWT token to check expiry
    const payload = JSON.parse(atob(token.split(".")[1]));
    const currentTime = Math.floor(Date.now() / 1000);

    if (payload.exp && payload.exp < currentTime) {
      // Remove session refresh listeners before logout
      removeSessionRefreshListeners();

      localStorage.removeItem("token");
      localStorage.removeItem("user");
      // Store expiration reason for login page
      localStorage.setItem("logoutReason", "session_expired");
      window.location.href = "/login";
    } else {
      // Token is still valid
    }
  } catch (error) {
    console.error("Error checking token expiry:", error);
    // If we can't decode the token, remove it for safety
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    window.location.href = "/login";
  }
};

// Check token expiry every 10 seconds for better responsiveness with 2-minute expiry
setInterval(checkTokenExpiry, 10000); // 10000ms = 10 seconds

// Function to refresh session on user activity (resets 2-minute timer)
let refreshThrottle = false;
const refreshSessionOnActivity = async () => {
  // Throttle to prevent too many API calls (max 1 per 30 seconds)
  if (!refreshThrottle) {
    refreshThrottle = true;

    // Check current token
    const token = localStorage.getItem("token");
    if (!token) {
      // Remove listeners since there's no token
      removeSessionRefreshListeners();

      refreshThrottle = false;
      return;
    }

    // Check token expiry
    try {
      const payload = JSON.parse(atob(token.split(".")[1]));
      const currentTime = Math.floor(Date.now() / 1000);
      const remainingTime = payload.exp - currentTime;

      if (remainingTime <= 0) {
        refreshThrottle = false;
        return;
      }
    } catch (error) {
      refreshThrottle = false;
      return;
    }

    try {
      const response = await api.post("/auth/refresh-session");
      if (response.data.success) {
        localStorage.setItem("token", response.data.access_token);
      }
    } catch (error) {
      // Session refresh failed - this is handled by the interceptor
    }

    // Allow next refresh after 30 seconds
    setTimeout(() => {
      refreshThrottle = false;
    }, 30000);
  }
};

// Store event listener references so we can remove them later
let eventListenersAdded = false;

// Function to add event listeners for session refresh
const addSessionRefreshListeners = () => {
  if (eventListenersAdded) return; // Already added

  document.addEventListener("click", refreshSessionOnActivity);
  document.addEventListener("keypress", refreshSessionOnActivity);
  document.addEventListener("scroll", refreshSessionOnActivity);
  document.addEventListener("mousemove", refreshSessionOnActivity);
  document.addEventListener("touchstart", refreshSessionOnActivity);

  eventListenersAdded = true;
};

// Function to remove event listeners for session refresh
const removeSessionRefreshListeners = () => {
  if (!eventListenersAdded) return; // Already removed

  document.removeEventListener("click", refreshSessionOnActivity);
  document.removeEventListener("keypress", refreshSessionOnActivity);
  document.removeEventListener("scroll", refreshSessionOnActivity);
  document.removeEventListener("mousemove", refreshSessionOnActivity);
  document.removeEventListener("touchstart", refreshSessionOnActivity);

  eventListenersAdded = false;
};

// Add listeners after 2 seconds (when user should be logged in)
setTimeout(() => {
  // Only add listeners if there's a valid token
  const token = localStorage.getItem("token");
  if (token) {
    addSessionRefreshListeners();
  }
}, 2000);

// Reset timer when page becomes visible (user switches back to tab)
document.addEventListener("visibilitychange", () => {
  if (!document.hidden) {
    checkTokenExpiry();
    // Only refresh if listeners are active (user is logged in)
    if (eventListenersAdded) {
      refreshSessionOnActivity();
    }
  }
});

// Auth API
export const login = async (email, password) => {
  try {
    const response = await api.post("/auth/login", { email, password });
    const data = response.data;

    // Store token and user info
    localStorage.setItem("token", data.access_token);
    localStorage.setItem(
      "user",
      JSON.stringify({
        id: data.user_id,
        email: data.email,
        full_name: data.full_name,
        role: data.role,
        organization_role: data.organization_role,
        organization_id: data.organization_id,
        admin_id: data.admin_id,
      })
    );

    // Add session refresh listeners after successful login
    addSessionRefreshListeners();

    return {
      token: data.access_token,
      user: {
        id: data.user_id,
        email: data.email,
        full_name: data.full_name,
        role: data.role,
        organization_role: data.organization_role,
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
    const response = await api.get("/auth/profile");
    return response.data;
  } catch (error) {
    throw new Error("Failed to get user info");
  }
};

export const getMyOrganization = async () => {
  try {
    const response = await api.get("/auth/my-organization");
    return response.data;
  } catch (error) {
    console.error(
      "Get my organization error:",
      error.response?.data?.detail || error.message
    );
    throw new Error(
      error.response?.data?.detail || "Failed to get organization info"
    );
  }
};

export const getMyAdmin = async () => {
  try {
    const response = await api.get("/auth/my-admin");
    return response.data;
  } catch (error) {
    console.error(
      "Get my admin error:",
      error.response?.data?.detail || error.message
    );
    throw new Error(error.response?.data?.detail || "Failed to get admin info");
  }
};

export const setPassword = async (email, password) => {
  try {
    const response = await api.post("/auth/set-password", {
      email,
      password,
    });
    return response.data;
  } catch (error) {
    throw new Error(extractErrorMessage(error, "Failed to set password"));
  }
};

export const changePassword = async (currentPassword, newPassword) => {
  try {
    const response = await api.post("/auth/change-password", {
      current_password: currentPassword,
      new_password: newPassword,
    });
    return response.data;
  } catch (error) {
    throw new Error(extractErrorMessage(error, "Failed to change password"));
  }
};

export const logout = async () => {
  try {
    await api.post("/auth/logout");
  } catch (error) {
    console.error("Logout error:", error);
  } finally {
    // Remove session refresh listeners before clearing localStorage
    removeSessionRefreshListeners();

    // Always clear localStorage regardless of API call success
    localStorage.clear();
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

export const getOrganizationStats = async () => {
  try {
    const response = await api.get("/documents/stats/organization");
    return response.data;
  } catch (error) {
    console.error("Organization stats error:", error);
    return {
      total_documents: 0,
      organization_id: null,
    };
  }
};

export const debugOrganizationDocuments = async () => {
  try {
    const response = await api.get("/documents/debug/organization");
    return response.data;
  } catch (error) {
    console.error("Debug organization error:", error);
    return null;
  }
};

// Feedback API
export const submitFeedback = async (feedbackData) => {
  try {
    const response = await api.post("/feedback/submit", feedbackData);
    return response.data;
  } catch (error) {
    console.error(
      "Submit feedback error:",
      error.response?.data?.detail || error.message
    );
    throw new Error(
      error.response?.data?.detail || "Failed to submit feedback"
    );
  }
};

export const getMyFeedback = async () => {
  try {
    const response = await api.get("/feedback/my-feedback");
    return response.data;
  } catch (error) {
    console.error(
      "Get my feedback error:",
      error.response?.data?.detail || error.message
    );
    throw new Error(error.response?.data?.detail || "Failed to get feedback");
  }
};

export const getUsersFeedback = async () => {
  try {
    const response = await api.get("/feedback/admin/users-feedback");
    return response.data;
  } catch (error) {
    console.error(
      "Get users feedback error:",
      error.response?.data?.detail || error.message
    );
    throw new Error(
      error.response?.data?.detail || "Failed to get users feedback"
    );
  }
};

export const getFeedbackStats = async () => {
  try {
    const response = await api.get("/feedback/admin/feedback-stats");
    return response.data;
  } catch (error) {
    console.error(
      "Get feedback stats error:",
      error.response?.data?.detail || error.message
    );
    throw new Error(
      error.response?.data?.detail || "Failed to get feedback statistics"
    );
  }
};

// Chat History API functions
export const getUserSessions = async () => {
  try {
    const response = await api.get("/chat-history/sessions");
    return response.data;
  } catch (error) {
    console.error(
      "Get user sessions error:",
      error.response?.data?.detail || error.message
    );
    throw new Error(
      error.response?.data?.detail || "Failed to get user sessions"
    );
  }
};

export const getSessionHistory = async (sessionId) => {
  try {
    const response = await api.get(`/chat-history/sessions/${sessionId}`);
    return response.data;
  } catch (error) {
    console.error(
      "Get session history error:",
      error.response?.data?.detail || error.message
    );
    throw new Error(
      error.response?.data?.detail || "Failed to get session history"
    );
  }
};

export const deleteSession = async (sessionId) => {
  try {
    const response = await api.delete(`/chat-history/sessions/${sessionId}`);
    return response.data;
  } catch (error) {
    console.error(
      "Delete session error:",
      error.response?.data?.detail || error.message
    );
    throw new Error(error.response?.data?.detail || "Failed to delete session");
  }
};

export default api;
