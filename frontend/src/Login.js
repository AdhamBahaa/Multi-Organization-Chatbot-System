import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { login } from "./api";
import "./Login.css";

const Login = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const result = await login(email, password);
      console.log("Login successful:", result);

      // Redirect to dashboard
      navigate("/dashboard");
    } catch (err) {
      // Check if this is a password setup required error
      if (err.message.includes("Password not set")) {
        // Redirect to password setup page with email parameter
        navigate(`/setup-password?email=${encodeURIComponent(email)}`);
      } else {
        setError(err.message);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <h1>🤖 RAG Chatbot</h1>
          <p>Sign in to your account</p>
        </div>

        {error && <div className="error-message">{error}</div>}

        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="Enter your email"
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              placeholder="Enter your password"
            />
          </div>

          <button type="submit" className="login-button" disabled={loading}>
            {loading ? "Signing in..." : "Sign In"}
          </button>
        </form>

        <div className="login-footer">
          <p>Demo Credentials:</p>
          <div className="demo-credentials">
            <div>
              <strong>Super Admin:</strong>
              <br />
              Email: superadmin@system.com
              <br />
              Password: superadmin123
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
