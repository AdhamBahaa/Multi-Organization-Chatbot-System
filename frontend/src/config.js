// Configuration for different environments
const config = {
  // Development (localhost)
  development: {
    API_BASE: "http://localhost:8002/api",
    FRONTEND_URL: "http://localhost:3000",
  },

  // Production (your hosted backend)
  production: {
    API_BASE: "https://your-backend-domain.com/api", // You'll update this
    FRONTEND_URL: "https://your-frontend-domain.com", // You'll update this
  },
};

// Get current environment
const environment = process.env.NODE_ENV || "development";

// Export current config
export const API_BASE = config[environment].API_BASE;
export const FRONTEND_URL = config[environment].FRONTEND_URL;

// For easy switching during development
export const isDevelopment = environment === "development";
export const isProduction = environment === "production";

console.log(`🌍 Environment: ${environment}`);
console.log(`🔗 API Base: ${API_BASE}`);
