import React, { useState } from "react";
import { useWebSocket } from "../hooks/useWebSocket";

/**
 * LiveTelemetry Component.
 * Demonstrates:
 *   1. WebSocket / Real-Time Full-Duplex Communication in React
 *   2. Custom hook integration (useWebSocket)
 *   3. Real-time data streaming without polling
 *   4. Bi-directional WebSocket command dispatch & status feedback
 *   5. Connection indicator badge & heartbeat metrics
 */
export default function LiveTelemetry() {
  const { isConnected, connectionStatus, lastMessage, messages, sendMessage } = useWebSocket(
    "ws://127.0.0.1:5000/ws/telemetry"
  );

  const [commandInput, setCommandInput] = useState("");
  const [dispatchedHistory, setDispatchedHistory] = useState([]);

  const handleSendCommand = (e) => {
    e.preventDefault();
    if (!commandInput.trim()) return;

    const payload = {
      type: "DISPATCH_COMMAND",
      commandId: `cmd_${Date.now()}`,
      payload: commandInput.trim(),
      timestamp: Date.now()
    };

    const success = sendMessage(payload);
    if (success) {
      setDispatchedHistory((prev) => [
        { id: payload.commandId, text: payload.payload, sentAt: new Date().toLocaleTimeString() },
        ...prev.slice(0, 4)
      ]);
      setCommandInput("");
    }
  };

  const metrics = lastMessage?.metrics || {
    serverUptimeSeconds: 0,
    memoryHeapUsedMb: 0,
    activeWebSocketClients: 0,
    systemStatus: "CONNECTING..."
  };

  return (
    <div className="card" style={{ marginTop: "24px", borderColor: isConnected ? "#00ff88" : "#f59e0b" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
        <div>
          <h2 style={{ margin: 0, fontSize: "18px", color: "#00e5ff" }}>
            ◈ REAL-TIME WEBSOCKET TELEMETRY
          </h2>
          <p style={{ margin: "4px 0 0 0", fontSize: "12px", color: "#94a3b8" }}>
            Full-duplex bidirectional stream powered by Native WebSocket & ws protocol
          </p>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <span
            style={{
              display: "inline-block",
              width: "10px",
              height: "10px",
              borderRadius: "50%",
              backgroundColor: isConnected ? "#00ff88" : "#ef4444",
              boxShadow: isConnected ? "0 0 8px #00ff88" : "none"
            }}
          />
          <span style={{ fontSize: "12px", fontWeight: "bold", color: isConnected ? "#00ff88" : "#ef4444" }}>
            {isConnected ? "CONNECTED (Live Stream)" : `DISCONNECTED (${connectionStatus})`}
          </span>
        </div>
      </div>

      {/* Real-Time Metrics Grid */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: "12px", marginBottom: "20px" }}>
        <div style={{ background: "#0b1220", padding: "12px", borderRadius: "6px", border: "1px solid #1e293b" }}>
          <div style={{ fontSize: "11px", color: "#64748b", textTransform: "uppercase" }}>Uptime</div>
          <div style={{ fontSize: "18px", fontWeight: "bold", color: "#00e5ff", marginTop: "2px" }}>
            {metrics.serverUptimeSeconds}s
          </div>
        </div>

        <div style={{ background: "#0b1220", padding: "12px", borderRadius: "6px", border: "1px solid #1e293b" }}>
          <div style={{ fontSize: "11px", color: "#64748b", textTransform: "uppercase" }}>V8 Heap Used</div>
          <div style={{ fontSize: "18px", fontWeight: "bold", color: "#a855f7", marginTop: "2px" }}>
            {metrics.memoryHeapUsedMb} MB
          </div>
        </div>

        <div style={{ background: "#0b1220", padding: "12px", borderRadius: "6px", border: "1px solid #1e293b" }}>
          <div style={{ fontSize: "11px", color: "#64748b", textTransform: "uppercase" }}>Active WS Clients</div>
          <div style={{ fontSize: "18px", fontWeight: "bold", color: "#00ff88", marginTop: "2px" }}>
            {metrics.activeWebSocketClients}
          </div>
        </div>

        <div style={{ background: "#0b1220", padding: "12px", borderRadius: "6px", border: "1px solid #1e293b" }}>
          <div style={{ fontSize: "11px", color: "#64748b", textTransform: "uppercase" }}>Stream Status</div>
          <div style={{ fontSize: "16px", fontWeight: "bold", color: "#f59e0b", marginTop: "4px" }}>
            {metrics.systemStatus}
          </div>
        </div>
      </div>

      {/* Real-time Bidirectional Command Form */}
      <form onSubmit={handleSendCommand} style={{ display: "flex", gap: "8px", marginBottom: "16px" }}>
        <input
          type="text"
          value={commandInput}
          onChange={(e) => setCommandInput(e.target.value)}
          placeholder="Send real-time frame over WebSocket (e.g. calibrate sensors)..."
          disabled={!isConnected}
          style={{
            flex: 1,
            padding: "10px 14px",
            backgroundColor: "#0b1220",
            border: "1px solid #334155",
            borderRadius: "6px",
            color: "#e2e8f0",
            fontSize: "13px"
          }}
        />
        <button
          type="submit"
          disabled={!isConnected || !commandInput.trim()}
          style={{
            padding: "10px 18px",
            backgroundColor: isConnected ? "#00e5ff" : "#334155",
            color: "#070b12",
            border: "none",
            borderRadius: "6px",
            fontWeight: "bold",
            cursor: isConnected ? "pointer" : "not-allowed"
          }}
        >
          Send Frame
        </button>
      </form>

      {/* Dispatched History & Last Received Payload */}
      {dispatchedHistory.length > 0 && (
        <div style={{ background: "#070b12", padding: "10px 14px", borderRadius: "6px", border: "1px solid #1e293b", fontSize: "12px" }}>
          <span style={{ color: "#64748b" }}>Recent Frames Sent via WebSocket: </span>
          <span style={{ color: "#00e5ff" }}>{dispatchedHistory.map((d) => d.text).join(" • ")}</span>
        </div>
      )}
    </div>
  );
}
