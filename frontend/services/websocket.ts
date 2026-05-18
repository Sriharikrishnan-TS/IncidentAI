/**
 * WebSocket Service
 *
 * Handles real-time WebSocket connections for live updates
 * Supports mock event simulation for development
 */

// Allow arbitrary event type strings to match backend event naming
type WebSocketEventType = string;

interface WebSocketEvent {
  type: WebSocketEventType;
  data: any;
  timestamp: string;
}

type EventHandler = (event: WebSocketEvent) => void;

const getWebSocketUrl = (): string => {
  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8080";
  const url = new URL(backendUrl);
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  url.pathname = "/ws";
  url.search = "";
  return url.toString();
};

/**
 * WebSocket Manager
 */
class WebSocketManager {
  private ws: WebSocket | null = null;
  private handlers: Map<WebSocketEventType, Set<EventHandler>> = new Map();
  private anyHandlers: Set<EventHandler> = new Set();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private useMock: boolean;
  private mockIntervals: NodeJS.Timeout[] = [];

  constructor() {
    this.useMock = process.env.NEXT_PUBLIC_USE_MOCK !== "false";
  }

  /**
   * Connect to WebSocket server
   */
  connect(repo_id?: string): void {
    if (this.useMock) {
      console.log("[WebSocket] Using mock mode");
      this.startMockEvents(repo_id);
      return;
    }

    const wsUrl = getWebSocketUrl();
    const url = repo_id ? `${wsUrl}?repo_id=${repo_id}` : wsUrl;

    try {
      this.ws = new WebSocket(url);

      this.ws.onopen = () => {
        console.log("[WebSocket] Connected");
        this.reconnectAttempts = 0;
      };

      this.ws.onmessage = (event) => {
        try {
          const raw = JSON.parse(event.data);

          // Support backend event shape ({ event: "...", repo_id: "...", ... })
          const eventType: WebSocketEventType = raw.type || raw.event || "unknown";
          const payload = raw.data ?? raw;
          const message: WebSocketEvent = {
            type: eventType,
            data: payload,
            timestamp: raw.timestamp || new Date().toISOString(),
          };

          this.handleEvent(message);
        } catch (error) {
          console.error("[WebSocket] Failed to parse message:", error);
        }
      };

      this.ws.onerror = (error) => {
        console.error("[WebSocket] Error:", error);
      };

      this.ws.onclose = () => {
        console.log("[WebSocket] Disconnected");
        this.attemptReconnect(repo_id);
      };
    } catch (error) {
      console.error("[WebSocket] Connection failed:", error);
      this.attemptReconnect(repo_id);
    }
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    // Clear mock intervals
    this.mockIntervals.forEach((interval) => clearInterval(interval));
    this.mockIntervals = [];
  }

  /**
   * Subscribe to an event type
   */
  on(eventType: WebSocketEventType, handler: EventHandler): () => void {
    if (!this.handlers.has(eventType)) {
      this.handlers.set(eventType, new Set());
    }
    this.handlers.get(eventType)!.add(handler);

    // Return unsubscribe function
    return () => {
      const handlers = this.handlers.get(eventType);
      if (handlers) {
        handlers.delete(handler);
      }
    };
  }

  /**
   * Subscribe to all events (receives every event)
   */
  onAny(handler: EventHandler): () => void {
    this.anyHandlers.add(handler);
    return () => {
      this.anyHandlers.delete(handler);
    };
  }

  /**
   * Unsubscribe from an event type
   */
  off(eventType: WebSocketEventType, handler: EventHandler): void {
    const handlers = this.handlers.get(eventType);
    if (handlers) {
      handlers.delete(handler);
    }
  }

  /**
   * Send a message to the server
   */
  send(data: any): void {
    if (this.useMock) {
      console.log("[WebSocket] Mock send:", data);
      return;
    }

    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      console.warn("[WebSocket] Cannot send, not connected");
    }
  }

  /**
   * Handle incoming event
   */
  private handleEvent(event: WebSocketEvent): void {
    console.log("[WebSocket] Event received:", event.type);

    const handlers = this.handlers.get(event.type);
    if (handlers) {
      handlers.forEach((handler) => {
        try {
          handler(event);
        } catch (error) {
          console.error("[WebSocket] Handler error:", error);
        }
      });
    }

    // Call any-handlers
    if (this.anyHandlers.size > 0) {
      this.anyHandlers.forEach((handler) => {
        try {
          handler(event);
        } catch (error) {
          console.error("[WebSocket] Any-handler error:", error);
        }
      });
    }
  }

  /**
   * Attempt to reconnect
   */
  private attemptReconnect(repo_id?: string): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error("[WebSocket] Max reconnection attempts reached");
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

    console.log(
      `[WebSocket] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`,
    );

    setTimeout(() => {
      this.connect(repo_id);
    }, delay);
  }

  /**
   * Start mock event simulation
   */
  private startMockEvents(repo_id?: string): void {
    // Simulate periodic events for testing
    const interval = setInterval(() => {
      const mockEvents: WebSocketEvent[] = [
        {
          type: "repo_analysis_progress",
          data: { progress: Math.floor(Math.random() * 100), repo_id },
          timestamp: new Date().toISOString(),
        },
      ];

      const randomEvent =
        mockEvents[Math.floor(Math.random() * mockEvents.length)];
      this.handleEvent(randomEvent);
    }, 10000); // Every 10 seconds

    this.mockIntervals.push(interval);
  }

  /**
   * Simulate a specific mock event (for testing)
   */
  simulateMockEvent(type: WebSocketEventType, data: any): void {
    if (!this.useMock) {
      console.warn("[WebSocket] simulateMockEvent only works in mock mode");
      return;
    }

    const event: WebSocketEvent = {
      type,
      data,
      timestamp: new Date().toISOString(),
    };

    this.handleEvent(event);
  }

  /**
   * Check if connected
   */
  isConnected(): boolean {
    if (this.useMock) {
      return true;
    }
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }
}

// Export singleton instance
export const wsManager = new WebSocketManager();

// Export types
export type { WebSocketEvent, WebSocketEventType, EventHandler };

// Made with Bob
