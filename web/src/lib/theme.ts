import { create } from "zustand";

type Theme = "dark" | "light";

interface ThemeState {
  theme: Theme;
  toggle: () => void;
}

export const useThemeStore = create<ThemeState>((set) => ({
  theme:
    typeof window !== "undefined" &&
    localStorage.getItem("clawdr-theme") === "light"
      ? "light"
      : "dark",

  toggle: () =>
    set((s) => {
      const next: Theme = s.theme === "dark" ? "light" : "dark";
      if (typeof window !== "undefined") {
        localStorage.setItem("clawdr-theme", next);
      }
      return { theme: next };
    }),
}));
