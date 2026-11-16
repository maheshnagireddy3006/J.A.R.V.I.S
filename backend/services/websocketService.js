/**
 * J.A.R.V.I.S. ECOSYSTEM - WEBSOCKET & REAL-TIME COMMUNICATION SERVICE
 * Demonstrates:
 *   1. WebSocket Server Initialization (ws.Server attached to HTTP server)
 *   2. Real-Time Full-Duplex Bidirectional Communication
 *   3. Client Lifecycle Management (Connection, Heartbeat Ping/Pong, Disconnection)
 *   4. Broadcast Telemetry Streaming to Connected Clients
 *   5. Inbound Command Dispatching and Live Event Notifications
 */

const WebSocket = require("ws");

class WebSocketService {
  constructor() {
    this.wss = null;
    this.clients = new Set();
    this.heartbeatInterval = null;
    this.telemetryInterval = null;
    this.telemetrySubscribers = new Set();
  }

  /**
   * Attaches WebSocket server to an existing HTTP/HTTPS server instance.
   * @param {import('http').Server} httpServer
   * @param {string} endpoint
   */
  initialize(httpServer, endpoint = "/ws/telemetry") {
    this.wss = new WebSocket.Server({
      server: httpServer,
      path: endpoint
    });

    console.log(`[WebSocket] Server mounted on endpoint: ${endpoint}`);

    this.wss.on("connection", (ws, req) => {
      this.handleConnection(ws, req);
    });

    // Start 30-second ping heartbeat to detect stale clients
    this.heartbeatInterval = setInterval(() => {
      this.wss.clients.forEach((ws) => {
        if (ws.isAlive === false) {
          this.clients.delete(ws);
          return ws.terminate();
        }
        ws.isAlive = false;
        ws.ping();
      });
    }, 30000);

    // Start 2-second real-time telemetry broadcast pulse
    this.telemetryInterval = setInterval(() => {
      this.broadcastTelemetry();
    }, 2000);

    this.wss.on("close", () => {
      clearInterval(this.heartbeatInterval);
      clearInterval(this.telemetryInterval);
    });
  }

  /**
   * Handles incoming new WebSocket client connections.
   * @param {WebSocket} ws
   * @param {import('http').IncomingMessage} req
   */
  handleConnection(ws, req) {
    ws.isAlive = true;
    ws.connectedAt = Date.now();
    ws.clientIp = req.socket.remoteAddress || "127.0.0.1";
    this.clients.add(ws);

    console.log(`[WebSocket] Client connected from ${ws.clientIp}. Total active: ${this.clients.size}`);

    // Send immediate initial handshake frame
    ws.send(JSON.stringify({
      type: "CONNECTION_ESTABLISHED",
      channel: "telemetry",
      clientIp: ws.clientIp,
      timestamp: Date.now(),
      protocol: "JARVIS-WS-V2",
      activeSubscribers: this.clients.size
    }));

    // Setup heartbeat pong response
    ws.on("pong", () => {
      ws.isAlive = true;
    });

    // Handle inbound client messages
    ws.on("message", (rawMessage) => {
      this.handleMessage(ws, rawMessage);
    });

    // Handle socket errors gracefully
    ws.on("error", (error) => {
      console.error(`[WebSocket] Error from client ${ws.clientIp}:`, error.message);
    });

    // Handle client disconnect
    ws.on("close", (code, reason) => {
      this.clients.delete(ws);
      console.log(`[WebSocket] Client disconnected (${code}). Remaining active: ${this.clients.size}`);
    });
  }

  /**
   * Routes and processes inbound messages from clients.
   * @param {WebSocket} ws
   * @param {Buffer|string} rawMessage
   */
  handleMessage(ws, rawMessage) {
    try {
      const data = JSON.parse(rawMessage.toString());

      switch (data.type) {
        case "PING":
          ws.send(JSON.stringify({ type: "PONG", timestamp: Date.now() }));
          break;

        case "SUBSCRIBE_TELEMETRY":
          this.telemetrySubscribers.add(ws);
          ws.send(JSON.stringify({
            type: "SUBSCRIPTION_CONFIRMED",
            stream: "realtime_hardware_telemetry",
            timestamp: Date.now()
          }));
          break;

        case "DISPATCH_COMMAND":
          // Echo command execution status in real-time
          ws.send(JSON.stringify({
            type: "COMMAND_STATUS",
            commandId: data.commandId || `cmd_${Date.now()}`,
            status: "PROCESSING",
            timestamp: Date.now()
          }));

          setTimeout(() => {
            if (ws.readyState === WebSocket.OPEN) {
              ws.send(JSON.stringify({
                type: "COMMAND_STATUS",
                commandId: data.commandId || `cmd_${Date.now()}`,
                status: "COMPLETED",
                result: `Command '${data.payload || "unknown"}' successfully executed at edge.`,
                timestamp: Date.now()
              }));
            }
          }, 800);
          break;

        default:
          ws.send(JSON.stringify({
            type: "ACK",
            receivedType: data.type,
            timestamp: Date.now()
          }));
      }
    } catch (err) {
      ws.send(JSON.stringify({
        type: "ERROR",
        message: "Invalid JSON frame received",
        timestamp: Date.now()
      }));
    }
  }

  /**
   * Broadcasts payload to all currently connected clients.
   * @param {object} payload
   */
  broadcast(payload) {
    const serialized = JSON.stringify(payload);
    for (const client of this.clients) {
      if (client.readyState === WebSocket.OPEN) {
        client.send(serialized);
      }
    }
  }

  /**
   * Broadcasts real-time system metrics to all connected clients.
   */
  broadcastTelemetry() {
    if (this.clients.size === 0) return;

    const memoryUsage = process.memoryUsage();
    const telemetryPayload = {
      type: "TELEMETRY_PULSE",
      timestamp: Date.now(),
      metrics: {
        serverUptimeSeconds: Math.floor(process.uptime()),
        memoryHeapUsedMb: +(memoryUsage.heapUsed / 1024 / 1024).toFixed(2),
        memoryHeapTotalMb: +(memoryUsage.heapTotal / 1024 / 1024).toFixed(2),
        memoryRssMb: +(memoryUsage.rss / 1024 / 1024).toFixed(2),
        activeWebSocketClients: this.clients.size,
        systemStatus: "OPTIMAL",
        gpuVramDedicated: "6GB Nvidia RTX 4050 (Reserved for Ollama LLM)"
      }
    };

    this.broadcast(telemetryPayload);
  }

  /**
   * Returns current connection telemetry for REST API inspection.
   */
  getStats() {
    return {
      activeConnections: this.clients.size,
      endpoint: "/ws/telemetry",
      protocol: "ws",
      heartbeatIntervalMs: 30000,
      telemetryPulseIntervalMs: 2000
    };
  }
}

// Export singleton instance
const webSocketService = new WebSocketService();

module.exports = {
  webSocketService,
  WebSocketService
};
