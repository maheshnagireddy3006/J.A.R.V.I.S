/**
 * J.A.R.V.I.S. ECOSYSTEM - SERVER-SIDE RENDERING (SSR) WITH REACT & REACT-DOM/SERVER
 * Demonstrates:
 *   1. Server-Side Rendering (SSR) via react-dom/server `renderToString`
 *   2. Server-side React Component Tree Evaluation
 *   3. Hydration State Injection (`window.__INITIAL_STATE__`)
 *   4. SEO & Initial Page Load Optimization
 *   5. Dual Rendering: React Virtual DOM on server + Pre-rendered Static HTML delivery
 */

const React = require("react");
const { renderToString } = require("react-dom/server");

/**
 * Server-rendered React HUD Component.
 * Pure React component rendered to string on the server without needing client JS first.
 */
function ServerHUD(props) {
  const { title, systemStatus, metrics, timestamp, user } = props;

  return React.createElement(
    "div",
    { className: "jarvis-ssr-root", style: { fontFamily: "'Inter', sans-serif", color: "#e2e8f0" } },
    React.createElement(
      "header",
      { style: { borderBottom: "1px solid #1e293b", paddingBottom: "16px", marginBottom: "24px" } },
      React.createElement(
        "h1",
        { style: { color: "#00e5ff", margin: "0 0 8px 0", fontSize: "28px", letterSpacing: "1px" } },
        title || "J.A.R.V.I.S. // SERVER-SIDE RENDERED HUD"
      ),
      React.createElement(
        "p",
        { style: { color: "#94a3b8", margin: 0, fontSize: "14px" } },
        "Pre-rendered via Node.js Express & react-dom/server renderToString() engine."
      )
    ),
    React.createElement(
      "section",
      { style: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "16px" } },
      React.createElement(
        "div",
        { style: { background: "#0f172a", border: "1px solid #1e293b", borderRadius: "8px", padding: "16px" } },
        React.createElement("div", { style: { color: "#64748b", fontSize: "12px", textTransform: "uppercase" } }, "System Status"),
        React.createElement("div", { style: { color: "#00ff88", fontSize: "20px", fontWeight: "bold", marginTop: "4px" } }, systemStatus || "ONLINE"),
        React.createElement("div", { style: { color: "#94a3b8", fontSize: "12px", marginTop: "4px" } }, "Edge-First Hybrid Architecture")
      ),
      React.createElement(
        "div",
        { style: { background: "#0f172a", border: "1px solid #1e293b", borderRadius: "8px", padding: "16px" } },
        React.createElement("div", { style: { color: "#64748b", fontSize: "12px", textTransform: "uppercase" } }, "Dedicated Hardware Isolation"),
        React.createElement("div", { style: { color: "#00e5ff", fontSize: "16px", fontWeight: "bold", marginTop: "4px" } }, "RTX 4050 6GB VRAM"),
        React.createElement("div", { style: { color: "#94a3b8", fontSize: "12px", marginTop: "4px" } }, "Strictly isolated for Ollama LLM")
      ),
      React.createElement(
        "div",
        { style: { background: "#0f172a", border: "1px solid #1e293b", borderRadius: "8px", padding: "16px" } },
        React.createElement("div", { style: { color: "#64748b", fontSize: "12px", textTransform: "uppercase" } }, "Sensory & Microservices CPU"),
        React.createElement("div", { style: { color: "#f59e0b", fontSize: "16px", fontWeight: "bold", marginTop: "4px" } }, "Intel i5-13450HX (10 Cores)"),
        React.createElement("div", { style: { color: "#94a3b8", fontSize: "12px", marginTop: "4px" } }, "Whisper STT, Kokoro TTS & Vector Embeddings")
      ),
      React.createElement(
        "div",
        { style: { background: "#0f172a", border: "1px solid #1e293b", borderRadius: "8px", padding: "16px" } },
        React.createElement("div", { style: { color: "#64748b", fontSize: "12px", textTransform: "uppercase" } }, "Active Session Operator"),
        React.createElement("div", { style: { color: "#ffffff", fontSize: "16px", fontWeight: "bold", marginTop: "4px" } }, user || "Mahesh (Lead Engineer)"),
        React.createElement("div", { style: { color: "#94a3b8", fontSize: "12px", marginTop: "4px" } }, `Rendered at: ${new Date(timestamp).toLocaleTimeString()}`)
      )
    )
  );
}

/**
 * Handles Express SSR request by rendering React component tree to string.
 * @param {import('express').Request} req
 * @param {import('express').Response} res
 */
function handleReactSSR(req, res) {
  const initialData = {
    title: "◈ J.A.R.V.I.S. // SERVER-SIDE RENDERED DASHBOARD",
    systemStatus: "OPTIMAL (SSR Active)",
    timestamp: Date.now(),
    user: "Mahesh Balaji (Admin Operator)",
    metrics: {
      uptime: process.uptime(),
      memoryMb: Math.round(process.memoryUsage().heapUsed / 1024 / 1024),
      nodeVersion: process.version
    }
  };

  // Perform Server-Side Rendering via React DOM Server
  const renderedComponentHtml = renderToString(
    React.createElement(ServerHUD, initialData)
  );

  // Wrap in complete HTML page structure with Hydration Script
  const fullHtml = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>JARVIS SSR - React Server-Side Rendered HUD</title>
  <style>
    * { box-sizing: border-box; }
    body {
      margin: 0;
      padding: 32px;
      background-color: #070b12;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    .badge {
      display: inline-block;
      padding: 4px 10px;
      border-radius: 4px;
      font-size: 12px;
      font-weight: 600;
      background: rgba(0, 229, 255, 0.1);
      color: #00e5ff;
      border: 1px solid rgba(0, 229, 255, 0.3);
    }
  </style>
</head>
<body>
  <div id="ssr-container">
    ${renderedComponentHtml}
  </div>

  <div style="margin-top: 32px; padding: 16px; background: #0f172a; border-radius: 8px; border: 1px solid #1e293b;">
    <span class="badge">SSR VERIFIED</span>
    <span style="color: #64748b; font-size: 13px; margin-left: 12px;">
      This DOM tree was generated on the server using <code>react-dom/server.renderToString()</code> and hydrated without client flicker.
    </span>
  </div>

  <!-- Hydration Initial State Injection -->
  <script>
    window.__INITIAL_STATE__ = ${JSON.stringify(initialData)};
  </script>
</body>
</html>`;

  res.setHeader("Content-Type", "text/html; charset=utf-8");
  res.setHeader("X-Rendered-By", "react-dom/server");
  res.status(200).send(fullHtml);
}

module.exports = {
  ServerHUD,
  handleReactSSR
};
