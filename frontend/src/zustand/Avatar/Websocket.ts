// zustand/sample.ts

import { create } from "zustand";

interface WebsocketState {
  isConnected: boolean;
  websocket: WebSocket | null;
  setwebsocket: (ws: WebSocket | null) => void;
  setIsConnected: (isConnected: boolean) => void;
}

const useWebsocket = create<WebsocketState>((set) => ({
  isConnected: false,
  websocket: null,
  setwebsocket: (ws: WebSocket | null) =>
    set(() => ({ websocket: ws })),
  setIsConnected: (isConnected: boolean) => set(() => ({ isConnected })),
}));

export default useWebsocket;
