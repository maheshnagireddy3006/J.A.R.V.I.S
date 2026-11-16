import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

/**
 * LoginForm Component.
 * Demonstrates:
 *   1. Form handling with Controlled Inputs
 *   2. Comprehensive Form Validation (Email format, Password length, Required constraints)
 *   3. Loading & Error UI States
 *   4. Programmatic Client-Side Routing via useNavigate()
 */
export default function LoginForm() {
  const navigate = useNavigate();

  // Controlled Form State
  const [formData, setFormData] = useState({
    email: "",
    password: ""
  });

  // Validation Errors State
  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [authError, setAuthError] = useState("");
  const [authSuccess, setAuthSuccess] = useState("");

  // Validation Logic
  const validate = (values) => {
    const errs = {};
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (!values.email.trim()) {
      errs.email = "Email address is required.";
    } else if (!emailRegex.test(values.email)) {
      errs.email = "Invalid email address format (e.g. user@domain.com).";
    }

    if (!values.password) {
      errs.password = "Password is required.";
    } else if (values.password.length < 6) {
      errs.password = "Password must be at least 6 characters long.";
    }

    return errs;
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    // Clear field-specific validation error on user input
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: "" }));
    }
    setAuthError("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const validationErrors = validate(formData);

    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }

    setIsSubmitting(true);
    setAuthError("");

    try {
      // Async API authentication request
      const response = await fetch("http://127.0.0.1:8000/api/v1/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: formData.email.split("@")[0],
          password: formData.password
        })
      });

      if (!response.ok) {
        throw new Error("Invalid credentials or server unreachable.");
      }

      const data = await response.json();
      setAuthSuccess("Authentication successful! Redirecting to Dashboard...");
      localStorage.setItem("jarvis_token", data.access_token);

      setTimeout(() => {
        navigate("/");
      }, 1000);
    } catch (err) {
      setAuthError(err.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div style={{ maxWidth: "440px", margin: "40px auto", padding: "24px", backgroundColor: "#0b1220", border: "1px solid #162540", borderRadius: "6px" }}>
      <h2 style={{ color: "#00e5ff", marginBottom: "8px", fontSize: "18px", letterSpacing: "1px" }}>
        ◈ OPERATOR AUTHENTICATION
      </h2>
      <p style={{ color: "#64748b", fontSize: "12px", marginBottom: "20px" }}>
        Sign in to access Jarvis Core Edge Control Interface.
      </p>

      {/* Error UI State */}
      {authError && (
        <div style={{ backgroundColor: "#2b0a14", border: "1px solid #ff2255", color: "#fca5a5", padding: "10px", borderRadius: "4px", fontSize: "12px", marginBottom: "16px" }}>
          ⚠ {authError}
        </div>
      )}

      {/* Success UI State */}
      {authSuccess && (
        <div style={{ backgroundColor: "#052e16", border: "1px solid #00ff88", color: "#86efac", padding: "10px", borderRadius: "4px", fontSize: "12px", marginBottom: "16px" }}>
          ✔ {authSuccess}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        {/* Email Field with Controlled Input & Validation */}
        <div className="form-group">
          <label className="form-label" htmlFor="email">Operator Email</label>
          <input
            id="email"
            name="email"
            type="email"
            value={formData.email}
            onChange={handleChange}
            placeholder="developer@stark.local"
            className={`form-input ${errors.email ? "error" : ""}`}
            disabled={isSubmitting}
          />
          {errors.email && <span className="form-error">⚠ {errors.email}</span>}
        </div>

        {/* Password Field with Controlled Input & Validation */}
        <div className="form-group">
          <label className="form-label" htmlFor="password">Security Password</label>
          <input
            id="password"
            name="password"
            type="password"
            value={formData.password}
            onChange={handleChange}
            placeholder="••••••••"
            className={`form-input ${errors.password ? "error" : ""}`}
            disabled={isSubmitting}
          />
          {errors.password && <span className="form-error">⚠ {errors.password}</span>}
        </div>

        {/* Loading UI State Button */}
        <button
          type="submit"
          disabled={isSubmitting}
          style={{
            width: "100%",
            marginTop: "10px",
            backgroundColor: isSubmitting ? "#162540" : "#00e5ff",
            color: isSubmitting ? "#64748b" : "#070b12",
            border: "none",
            borderRadius: "4px",
            padding: "12px",
            fontWeight: "bold",
            cursor: isSubmitting ? "not-allowed" : "pointer"
          }}
        >
          {isSubmitting ? "AUTHENTICATING..." : "SIGN IN"}
        </button>
      </form>
    </div>
  );
}
