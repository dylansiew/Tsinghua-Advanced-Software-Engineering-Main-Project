// zustand/sample.ts

import { v4 as uuidv4 } from "uuid";
import { create } from "zustand";
interface SessionInitializerState {
  sessionID: string | null;
  initialize: () => void;
}

const useSessionInitializer = create<SessionInitializerState>((set) => ({
  sessionID: null,
  initialize: () => set(() => ({ sessionID: uuidv4() })),
}));

export default useSessionInitializer;
