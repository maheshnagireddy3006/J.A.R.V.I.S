import React from "react";
import { BrowserRouter as Router, Routes, Route, Link, NavLink } from "react-router-dom";
import Dashboard from "./components/Dashboard";
import LoginForm from "./components/LoginForm";
import LiveTelemetry from "./components/LiveTelemetry";
import "./index.css";

/**
 * Root Application Component.
 * Demonstrates:
 *   1. Client-Side Routing via React Router (BrowserRouter, Routes, Route, Link, NavLink)
 *   2. Responsive Navigation Bar layout
 *   3. Component Composition across views
 */
export default function App() {
  return (
    <Router>
      <div style={{ minHeight: "100vh", backgroundColor: "#070b12" }}>
        {/* Navigation Bar with Client-Side Router Links */}
        <nav className="navbar">
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <span style={{ color: "#00e5ff", fontWeight: "bold", fontSize: "16px", letterSpacing: "1px" }}>
              ◈ J.A.R.V.I.S.
            </span>
            <span style={{ fontSize: "11px", color: "#64748b", textTransform: "uppercase" }}>
              Edge-First OS
            </span>
          </div>

          <div className="nav-links">
            <NavLink
              to="/"
              className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}
            >
              DASHBOARD
            </NavLink>
            <NavLink
              to="/realtime"
              className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}
            >
              WS TELEMETRY
            </NavLink>
            <NavLink
              to="/architecture"
              className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}
            >
              ARCHITECTURE SPEC
            </NavLink>
            <NavLink
              to="/login"
              className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}
            >
              OPERATOR LOGIN
            </NavLink>
          </div>
        </nav>

        {/* Client-Side Route Declarations */}
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/realtime" element={<div className="container"><LiveTelemetry /></div>} />
          <Route path="/login" element={<LoginForm />} />
          <Route
            path="/architecture"
            element={
              <div className="container">
                <div style={{ backgroundColor: "#0b1220", border: "1px solid #162540", padding: "32px", borderRadius: "6px" }}>
                  <h2 style={{ color: "#00e5ff", marginBottom: "16px" }}>
                    J.A.R.V.I.S. Edge-First Microservices Architecture
                  </h2>
                  <p style={{ lineHeight: "1.8", color: "#94a3b8", marginBottom: "16px" }}>
                    This system executes 100% locally on workstation hardware. The discrete Nvidia RTX 4050 GPU
                    is reserved exclusively for Ollama Llama 3.1 8B LLM reasoning, while RealtimeSTT (Whisper on CPU),
                    Kokoro-82M TTS, ChromaDB vector embeddings, and FastAPI/Express microservices run across dedicated CPU cores.
                  </p>
                  <Link
                    to="/"
                    style={{
                      display: "inline-block",
                      backgroundColor: "#00e5ff",
                      color: "#070b12",
                      padding: "8px 16px",
                      borderRadius: "4px",
                      textDecoration: "none",
                      fontWeight: "bold",
                      fontSize: "13px"
                    }}
                  >
                    ← Back to Live Dashboard
                  </Link>
                </div>
              </div>
            }
          />
        </Routes>
      </div>
    </Router>
  );
}
