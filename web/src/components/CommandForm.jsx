import React, { useState } from "react";

/**
 * Demonstrates:
 * - Controlled Inputs (useState bindings)
 * - Form Validation (pre-submit constraint checking)
 * - Loading & Error UI States
 */
export default function CommandForm({ onSubmitDirective, isLoading }) {
  const [directive, setDirective] = useState("");
  const [validationError, setValidationError] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    const clean = directive.trim();

    // Form Validation Rules
    if (!clean) {
      setValidationError("Directive cannot be empty.");
      return;
    }
    if (clean.length < 3) {
      setValidationError("Directive must be at least 3 characters long.");
      return;
    }

    setValidationError("");
    onSubmitDirective(clean);
    setDirective("");
  };

  return (
    <form
      onSubmit={handleSubmit}
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "8px",
        backgroundColor: "#0b1220",
        border: "1px solid #162540",
        borderRadius: "4px",
        padding: "16px"
      }}
    >
      <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
        <input
          type="text"
          value={directive}
          disabled={isLoading}
          onChange={(e) => {
            setDirective(e.target.value);
            if (validationError) setValidationError("");
          }}
          placeholder="Issue directive (e.g. 'Check hardware diagnostics', 'Open calculator')..."
          style={{
            flex: 1,
            backgroundColor: "#070b12",
            border: validationError ? "1px solid #ff2255" : "1px solid #162540",
            color: "#e2e8f0",
            padding: "12px 14px",
            fontSize: "14px",
            borderRadius: "4px",
            outline: "none",
            fontFamily: "monospace"
          }}
        />
        <button
          type="submit"
          disabled={isLoading}
          style={{
            backgroundColor: isLoading ? "#162540" : "#00e5ff",
            color: isLoading ? "#64748b" : "#070b12",
            border: "none",
            borderRadius: "4px",
            padding: "12px 24px",
            fontWeight: "bold",
            cursor: isLoading ? "not-allowed" : "pointer",
            transition: "all 0.2s ease"
          }}
        >
          {isLoading ? "PROCESSING..." : "TRANSMIT"}
        </button>
      </div>

      {/* Error UI State */}
      {validationError && (
        <span style={{ fontSize: "12px", color: "#ff2255", fontWeight: "500" }}>
          ⚠ {validationError}
        </span>
      )}
    </form>
  );
}
