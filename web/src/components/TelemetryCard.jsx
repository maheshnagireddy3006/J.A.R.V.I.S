import React from "react";

/**
 * Demonstrates:
 * - React Component Composition
 * - Props interface
 * - Responsive styling
 */
export default function TelemetryCard({ label, value, unit, colorHex, subtext }) {
  return (
    <div
      style={{
        backgroundColor: "#0b1220",
        border: "1px solid #162540",
        borderLeft: `4px solid ${colorHex || "#00e5ff"}`,
        borderRadius: "4px",
        padding: "16px",
        display: "flex",
        flexDirection: "column",
        gap: "6px",
        flex: "1 1 200px"
      }}
    >
      <span style={{ fontSize: "11px", textTransform: "uppercase", color: "#64748b", letterSpacing: "1px" }}>
        {label}
      </span>
      <div style={{ display: "flex", alignItems: "baseline", gap: "6px" }}>
        <span style={{ fontSize: "24px", fontWeight: "bold", color: "#e2e8f0", fontFamily: "monospace" }}>
          {value !== undefined && value !== null ? value : "--"}
        </span>
        {unit && <span style={{ fontSize: "13px", color: "#94a3b8" }}>{unit}</span>}
      </div>
      {subtext && <span style={{ fontSize: "12px", color: colorHex || "#00e5ff" }}>{subtext}</span>}
    </div>
  );
}
