"use client";

import { useThemeStore } from "@/lib/theme";

export function ThemeToggle() {
  const { theme, toggle } = useThemeStore();

  return (
    <button
      onClick={toggle}
      title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
      className="flex h-8 w-8 items-center justify-center rounded-full border border-border bg-surface-raised text-text-secondary transition-colors hover:border-border-hover hover:text-text-primary"
    >
      <span className="text-sm">{theme === "dark" ? "L" : "D"}</span>
    </button>
  );
}
