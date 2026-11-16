import React, { useState } from "react";
import Dashboard from "./components/Dashboard";

/**
 * Root Application Component.
 * Demonstrates:
 *   - Client-side Routing (state-based navigation between views)
 *   - Global layout management
 */
export default function App() {
  const [currentRoute, setCurrentRoute] = useState("dashboard"); // 'dashboard' | 'about'

  return (
    <div style={{ minHeight: "100vh", backgroundColor: "#070b12" }}>
      {/* Navigation Bar */}
      <nav style={{ backgroundColor: "#0b1220", borderBottom: "1px solid #162540", padding: "10px 24px", display: "flex", gap: "16px" }}>
        <button
          onClick={() => setCurrentRoute("dashboard")}
          style={{
            background: "transparent",
            border: "none",
            color: currentRoute === "dashboard" ? "#00e5ff" : "#64748b",
            fontWeight: "bold",
            cursor: "pointer",
            fontSize: "13px"
          }}
        >
          DASHBOARD
        </button>
        <button
          onClick={() => setCurrentRoute("architecture")}
          style={{
            background: "transparent",
            border: "none",
            color: currentRoute === "architecture" ? "#00e5ff" : "#64748b",
            fontWeight: "bold",
            cursor: "pointer",
            fontSize: "13px"
          }}
        >
          ARCHITECTURE SPEC
        </button>
      </nav>

      {/* Client-Side View Switcher */}
      {currentRoute === "dashboard" ? (
        <Dashboard />
      ) : (
        <div style={{ padding: "32px", maxWidth: "900px", margin: "0 auto", color: "#e2e8f0" }}>
          <h2 style={{ color: "#00e5ff", marginBottom: "16px" }}>J.A.R.V.I.S. Edge-First Architecture</h2>
          <p style={{ lineHeight: "1.7", color: "#94a3b8" }}>
            This system runs 100% locally on workstation hardware. The discrete Nvidia RTX 4050 GPU is reserved exclusively
            for Ollama Llama 3.1 8B LLM reasoning, while RealtimeSTT (Whisper on CPU), Kokoro-82M TTS, ChromaDB vector
            retrieval, and FastAPI services run across dedicated CPU worker threads.
          </p>
        </div>
      )}
    </div>
  );
}
