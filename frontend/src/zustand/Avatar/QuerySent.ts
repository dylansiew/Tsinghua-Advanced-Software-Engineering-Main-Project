// zustand/sample.ts

import { create } from "zustand";
interface QuerySentState {
  querySent: boolean;
  setQuerySent: (newQuerySent: boolean) => void;
}

const useQuerySent = create<QuerySentState>((set) => ({
  querySent: false,
  setQuerySent: (newQuerySent: boolean) =>
    set(() => ({ querySent: newQuerySent })),
}));

export default useQuerySent;
