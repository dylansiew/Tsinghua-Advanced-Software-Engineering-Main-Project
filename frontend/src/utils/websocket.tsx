import { useEffect, useRef } from "react";

const baseURL = import.meta.env.VITE_API_URL;

interface WebsocketManagerProps {
  onMessage: (event: MessageEvent) => void;
  url: string;
  setIsConnected: (isConnected: boolean) => void;
  isConnected: boolean;
  websocket: WebSocket | null;
  setwebsocket: (ws: WebSocket | null) => void;
}

const WebsocketManager: React.FC<WebsocketManagerProps> = ({
  onMessage,
  url,
  setIsConnected,
  isConnected,
  websocket,
  setwebsocket,
}) => {
  const reconnectTimeout = useRef<NodeJS.Timeout | null>(null);

  function connectWebSocket(): void {
    const websocketUrl = baseURL.replace("https", "wss");
    const ws = new WebSocket(`${websocketUrl}/${url}`);
    setwebsocket(ws);
    
    ws.onopen = () => {
      //   console.log("WebSocket connected");
      setIsConnected(true);
    };

    ws.onmessage = (event: MessageEvent) => {
      onMessage(event);
    };

    ws.onerror = (error: Event) => {
      console.error("WebSocket error:", error);
    };

    ws.onclose = () => {
      //   console.log("WebSocket disconnected");
      setIsConnected(false);

      // Try to reconnect after 2 seconds
      reconnectTimeout.current = setTimeout(() => {
        // console.log("Attempting to reconnect...");
        connectWebSocket();
      }, 2000);
    };
  }

  useEffect(() => {
    connectWebSocket();
    return () => {
      if (websocket) {
        websocket.close();
      }
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current);
      }
    };
  }, []);

  return null;
};

export default WebsocketManager;
