import React, { useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { setPassword as setPasswordAPI } from "./api";
import "./PasswordSetup.css";

const PasswordSetup = () => {
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  // Get email from URL parameters
  const email = searchParams.get("email");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    // Validate passwords
    if (password.length < 6) {
      setError("Password must be at least 6 characters long");
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    setLoading(true);

    try {
      await setPasswordAPI(email, password);
      setSuccess(true);

      // Redirect to login after 2 seconds
      setTimeout(() => {
        navigate("/login");
      }, 2000);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (!email) {
    return (
      <div className="password-setup-container">
        <div className="password-setup-card">
          <div className="error-message">
            <h2>Invalid Setup Link</h2>
            <p>
              This password setup link is invalid or missing the email
              parameter.
            </p>
            <button
              onClick={() => navigate("/login")}
              className="btn btn-primary"
            >
              Go to Login
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (success) {
    return (
      <div className="password-setup-container">
        <div className="password-setup-card">
          <div className="success-message">
            <h2>✅ Password Set Successfully!</h2>
            <p>
              Your password has been set. You will be redirected to the login
              page shortly.
            </p>
            <div className="loading-spinner"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="password-setup-container">
      <div className="password-setup-card">
        <div className="password-setup-header">
          <h1>🔐 Set Your Password</h1>
          <p>
            Welcome! Please set your password to complete your account setup.
          </p>
          <div className="user-info">
            <strong>Email:</strong> {email}
          </div>
        </div>

        {error && <div className="error-message">{error}</div>}

        <form onSubmit={handleSubmit} className="password-setup-form">
          <div className="form-group">
            <label htmlFor="password">New Password</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              placeholder="Enter your new password"
              minLength={6}
            />
            <small>Password must be at least 6 characters long</small>
          </div>

          <div className="form-group">
            <label htmlFor="confirmPassword">Confirm Password</label>
            <input
              type="password"
              id="confirmPassword"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              placeholder="Confirm your new password"
            />
          </div>

          <button
            type="submit"
            className="password-setup-button"
            disabled={loading}
          >
            {loading ? "Setting Password..." : "Set Password"}
          </button>
        </form>

        <div className="password-setup-footer">
          <p>
            Already have a password?{" "}
            <button onClick={() => navigate("/login")} className="link-button">
              Sign in here
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};

export default PasswordSetup;
