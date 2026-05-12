import { create } from "zustand";

type CanvasStore = {
  runStatus: "idle" | "running" | "success" | "error";
  logs: string[];
  setRunStatus: (status: CanvasStore["runStatus"]) => void;
  appendLog: (line: string) => void;
};

export const useCanvasStore = create<CanvasStore>((set) => ({
  runStatus: "idle",
  logs: [],
  setRunStatus: (runStatus) => set({ runStatus }),
  appendLog: (line) => set((state) => ({ logs: [...state.logs, line] })),
}));
