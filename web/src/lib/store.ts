import { create } from "zustand";
import type { ProjectView } from "./api";
import { fetchProjects } from "./api";

type ConnectionStatus = "connecting" | "connected" | "disconnected";

interface AppState {
  projects: ProjectView[];
  connectionStatus: ConnectionStatus;
  error: string | null;

  setProjects: (projects: ProjectView[]) => void;
  updateProjectState: (
    projectId: string,
    state: ProjectView["session_state"],
    extra?: { startedAt?: string | null; url?: string | null },
  ) => void;
  setConnectionStatus: (status: ConnectionStatus) => void;
  setError: (error: string | null) => void;
  loadProjects: () => Promise<void>;
}

export const useAppStore = create<AppState>((set) => ({
  projects: [],
  connectionStatus: "disconnected",
  error: null,

  setProjects: (projects) => set({ projects, error: null }),

  updateProjectState: (projectId, state, extra) =>
    set((s) => ({
      projects: s.projects.map((p) =>
        p.id === projectId
          ? {
              ...p,
              session_state: state,
              started_at: extra?.startedAt ?? p.started_at,
              session_url: extra?.url !== undefined ? extra.url : p.session_url,
            }
          : p,
      ),
    })),

  setConnectionStatus: (connectionStatus) => set({ connectionStatus }),

  setError: (error) => set({ error }),

  loadProjects: async () => {
    try {
      const projects = await fetchProjects();
      set({ projects, error: null });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : "Failed to load projects",
      });
    }
  },
}));
