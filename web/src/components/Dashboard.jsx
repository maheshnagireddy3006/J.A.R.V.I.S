import React, { useState, useEffect } from "react";
import TelemetryCard from "./TelemetryCard";
import CommandForm from "./CommandForm";
import TerminalConsole from "./TerminalConsole";

/**
 * Main Holographic Dashboard Component.
 * Demonstrates:
 *   1. React Component Composition
 *   2. State Management with useState (telemetry, logs, loading, errors)
 *   3. Side Effects with useEffect (periodic polling & cleanup)
 *   4. Async Data Fetching from API (fetch with async/await)
 *   5. Loading & Error UI States
 *   6. Responsive Layout & Modern Sci-Fi Styling
 */
export default function Dashboard() {
  const [telemetry, setTelemetry] = useState({
    cpu_percent: 0,
    ram_percent: 0,
    status: "CONNECTING",
    cache_hit_ratio: 0
  });
  const [logs, setLogs] = useState([
    {
      timestamp: new Date().toLocaleTimeString(),
      tag: "SYSTEM",
      message: "Web HUD Dashboard booted. Connecting to local Jarvis Core REST/WS API..."
    }
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const [networkError, setNetworkError] = useState(null);

  // Side Effects with useEffect: Periodic Async Polling
  useEffect(() => {
    let isMounted = true;

    async function fetchTelemetry() {
      try {
        const response = await fetch("http://127.0.0.1:8000/api/v1/health");
        if (!response.ok) {
          throw new Error(`Server returned HTTP ${response.status}`);
        }
        const data = await response.json();
        if (isMounted) {
          setTelemetry({
            cpu_percent: data.hardware?.cpu?.usage_percent || 0,
            ram_percent: data.hardware?.ram?.percent_used || 0,
            status: "ONLINE : IDLE",
            cache_hit_ratio: data.cache?.hit_ratio_percent || 0
          });
          setNetworkError(null);
        }
      } catch (err) {
        if (isMounted) {
          setTelemetry(prev => ({ ...prev, status: "OFFLINE / DISCONNECTED" }));
          setNetworkError("Cannot reach Jarvis Core REST API at http://127.0.0.1:8000. Is the server running?");
        }
      }
    }

    // Initial fetch
    fetchTelemetry();

    // Poll every 3 seconds
    const intervalId = setInterval(fetchTelemetry, 3000);

    // Cleanup on unmount
    return () => {
      isMounted = false;
      clearInterval(intervalId);
    };
  }, []);

  // Async Directive Execution
  const handleDirectiveSubmit = async (directiveText) => {
    setIsLoading(true);
    const now = new Date().toLocaleTimeString();

    // Append user command to log
    setLogs(prev => [
      ...prev,
      { timestamp: now, tag: "USER", message: directiveText }
    ]);

    try {
      // Mock / Operator token for API authorization
      const response = await fetch("http://127.0.0.1:8000/api/v1/agent/query", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": "Bearer mock-operator-token"
        },
        body: JSON.stringify({ query: directiveText })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || `HTTP ${response.status}`);
      }

      const result = await response.json();
      setLogs(prev => [
        ...prev,
        {
          timestamp: new Date().toLocaleTimeString(),
          tag: "JARVIS",
          message: result.response || "Operation completed."
        }
      ]);
    } catch (err) {
      setLogs(prev => [
        ...prev,
        {
          timestamp: new Date().toLocaleTimeString(),
          tag: "ERROR",
          message: `Execution failed: ${err.message}`
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ padding: "24px", maxWidth: "1280px", margin: "0 auto", display: "flex", flexDirection: "column", gap: "20px" }}>
      {/* Header */}
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid #162540", paddingBottom: "16px" }}>
        <div>
          <h1 style={{ fontSize: "20px", fontWeight: "bold", color: "#00e5ff", letterSpacing: "1px" }}>
            ◈ JARVIS // HOLOGRAPHIC WEB HUD
          </h1>
          <p style={{ fontSize: "12px", color: "#64748b" }}>
            Edge-First Graph-Agent Ecosystem • React & RESTful Integration
          </p>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <span
            style={{
              height: "10px",
              width: "10px",
              borderRadius: "50%",
              backgroundColor: telemetry.status.includes("ONLINE") ? "#00ff88" : "#ff2255",
              display: "inline-block"
            }}
          />
          <span style={{ fontSize: "12px", fontWeight: "bold", color: telemetry.status.includes("ONLINE") ? "#00ff88" : "#ff2255" }}>
            {telemetry.status}
          </span>
        </div>
      </header>

      {/* Network Alert (Error State) */}
      {networkError && (
        <div style={{ backgroundColor: "#2b0a14", border: "1px solid #ff2255", color: "#fca5a5", padding: "12px 16px", borderRadius: "4px", fontSize: "13px" }}>
          ⚠ {networkError}
        </div>
      )}

      {/* Responsive Telemetry Grid */}
      <div style={{ display: "flex", flexWrap: "wrap", gap: "16px" }}>
        <TelemetryCard label="CPU Utilization" value={telemetry.cpu_percent} unit="%" colorHex="#00e5ff" subtext="Intel i5-13450HX" />
        <TelemetryCard label="RAM Allocation" value={telemetry.ram_percent} unit="%" colorHex="#38bdf8" subtext="24GB High-Speed DDR5" />
        <TelemetryCard label="Cache Hit Ratio" value={telemetry.cache_hit_ratio} unit="%" colorHex="#00ff88" subtext="Redis / In-Memory Tier" />
        <TelemetryCard label="Neural Engine" value="Llama 3.1" unit="8B" colorHex="#a855f7" subtext="Ollama on RTX 4050 GPU" />
      </div>

      {/* Center Terminal Console */}
      <TerminalConsole logs={logs} onClear={() => setLogs([])} />

      {/* Bottom Command Form */}
      <CommandForm onSubmitDirective={handleDirectiveSubmit} isLoading={isLoading} />
    </div>
  );
}
