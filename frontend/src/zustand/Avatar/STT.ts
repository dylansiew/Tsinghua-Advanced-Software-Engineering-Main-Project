// zustand/sample.ts

import { create } from "zustand";

interface STTState {
  previousTranscript: string;
  transcript: string;
  spokenChunk: string;
  websocket: WebSocket | null;
  chunkConsumed: () => void;
  setTranscript: (newTranscript: string) => void;
}

const useSTT = create<STTState>((set, get) => ({
  previousTranscript: "",
  transcript: "",
  spokenChunk: "",
  websocket: null,
  chunkConsumed: () =>
    set(() => ({ previousTranscript: get().transcript, spokenChunk: "" })),
  setTranscript: (newTranscript: string) => {
    const newSpokenChunk = newTranscript.slice(get().previousTranscript.length);
    set(() => ({ transcript: newTranscript, spokenChunk: newSpokenChunk }));
  },
}));

export default useSTT;
