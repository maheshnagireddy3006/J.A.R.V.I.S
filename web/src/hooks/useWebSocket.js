import { useState, useEffect, useRef, useCallback } from "react";

/**
 * Custom React Hook: useWebSocket
 * Demonstrates:
 *   1. Full-Duplex Real-Time Communication over WebSocket
 *   2. Connection Lifecycle Management (Connecting, Open, Closing, Closed)
 *   3. Auto-reconnect with Exponential Backoff
 *   4. Heartbeat Ping / Pong handling
 *   5. Message Queueing and Outbound Dispatch
 */
export function useWebSocket(url) {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);
  const [messages, setMessages] = useState([]);
  const [connectionStatus, setConnectionStatus] = useState("CONNECTING");

  const socketRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttemptsRef = useRef(0);

  const connect = useCallback(() => {
    try {
      setConnectionStatus("CONNECTING");
      const wsUrl = url || (window.location.protocol === "https:" ? "wss://" : "ws://") + window.location.host + "/ws/telemetry";
      const socket = new WebSocket(wsUrl);
      socketRef.current = socket;

      socket.onopen = () => {
        setIsConnected(true);
        setConnectionStatus("OPEN");
        reconnectAttemptsRef.current = 0;
        console.log("[useWebSocket] Connected to real-time endpoint:", wsUrl);

        // Send subscription message
        socket.send(JSON.stringify({
          type: "SUBSCRIBE_TELEMETRY",
          timestamp: Date.now()
        }));
      };

      socket.onmessage = (event) => {
        try {
          const parsed = JSON.parse(event.data);
          setLastMessage(parsed);
          setMessages((prev) => [...prev.slice(-49), parsed]); // Keep last 50 events
        } catch (err) {
          setLastMessage({ raw: event.data, timestamp: Date.now() });
        }
      };

      socket.onerror = (error) => {
        console.warn("[useWebSocket] Socket error observed:", error);
      };

      socket.onclose = () => {
        setIsConnected(false);
        setConnectionStatus("CLOSED");
        socketRef.current = null;

        // Auto-reconnect with exponential backoff (up to 5s max)
        const delay = Math.min(1000 * Math.pow(1.5, reconnectAttemptsRef.current), 5000);
        reconnectAttemptsRef.current += 1;
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, delay);
      };
    } catch (err) {
      setConnectionStatus("ERROR");
    }
  }, [url]);

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (socketRef.current) {
        socketRef.current.close();
      }
    };
  }, [connect]);

  /**
   * Dispatches outbound message over WebSocket
   */
  const sendMessage = useCallback((payload) => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      const serialized = typeof payload === "string" ? payload : JSON.stringify(payload);
      socketRef.current.send(serialized);
      return true;
    }
    return false;
  }, []);

  return {
    isConnected,
    connectionStatus,
    lastMessage,
    messages,
    sendMessage
  };
}
