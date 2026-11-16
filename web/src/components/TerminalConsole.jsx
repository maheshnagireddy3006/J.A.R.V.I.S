import React from "react";

/**
 * Terminal Console component displaying timestamped log events.
 */
export default function TerminalConsole({ logs, onClear }) {
  const getTagColor = (tag) => {
    switch (tag) {
      case "JARVIS":
      case "SUCCESS":
        return "#00ff88";
      case "ERROR":
        return "#ff2255";
      case "RETRY":
      case "WARN":
        return "#ffaa00";
      case "MIC":
      case "AUDIO":
        return "#a855f7";
      case "ROUTER":
      case "TOOL":
        return "#38bdf8";
      default:
        return "#00e5ff";
    }
  };

  return (
    <div
      style={{
        backgroundColor: "#070b12",
        border: "1px solid #162540",
        borderRadius: "4px",
        display: "flex",
        flexDirection: "column",
        height: "380px"
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "10px 16px",
          borderBottom: "1px solid #162540",
          backgroundColor: "#0b1220"
        }}
      >
        <span style={{ fontSize: "12px", letterSpacing: "1px", color: "#64748b", textTransform: "uppercase" }}>
          ◈ Live Terminal Console Stream
        </span>
        <button
          onClick={onClear}
          style={{
            backgroundColor: "transparent",
            border: "1px solid #162540",
            color: "#64748b",
            padding: "4px 10px",
            fontSize: "11px",
            borderRadius: "3px",
            cursor: "pointer"
          }}
        >
          CLEAR
        </button>
      </div>

      <div
        style={{
          flex: 1,
          overflowY: "auto",
          padding: "14px",
          fontFamily: "monospace",
          fontSize: "13px",
          display: "flex",
          flexDirection: "column",
          gap: "6px"
        }}
      >
        {logs.length === 0 ? (
          <div style={{ color: "#475569", fontStyle: "italic" }}>
            Awaiting sensory events and directives...
          </div>
        ) : (
          logs.map((log, idx) => (
            <div key={idx} style={{ lineHeight: "1.5" }}>
              <span style={{ color: "#475569", marginRight: "8px" }}>[{log.timestamp}]</span>
              <span style={{ color: getTagColor(log.tag), fontWeight: "bold", marginRight: "8px" }}>
                [{log.tag}]
              </span>
              <span style={{ color: "#e2e8f0" }}>{log.message}</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
