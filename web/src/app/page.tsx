"use client";

import { useEffect } from "react";
import { ConnectionStatus } from "@/components/connection-status";
import { ProjectGrid } from "@/components/project-grid";
import { ThemeToggle } from "@/components/theme-toggle";
import { useAppStore } from "@/lib/store";
import { useThemeStore } from "@/lib/theme";
import { startWebSocket, stopWebSocket } from "@/lib/ws";

export default function Page() {
  const loadProjects = useAppStore((s) => s.loadProjects);
  const theme = useThemeStore((s) => s.theme);

  useEffect(() => {
    loadProjects();
    startWebSocket();
    return () => stopWebSocket();
  }, [loadProjects]);

  // Apply theme class to html element
  useEffect(() => {
    const html = document.documentElement;
    html.classList.toggle("light", theme === "light");
  }, [theme]);

  return (
    <main className="mx-auto max-w-5xl px-4 py-6 sm:px-6 sm:py-10">
      <header className="mb-6 flex items-center justify-between gap-3 sm:mb-8">
        <div className="min-w-0">
          <h1 className="text-2xl font-bold tracking-tight text-text-primary sm:text-3xl">
            ClawdR
          </h1>
          <p className="mt-0.5 text-xs text-text-muted sm:mt-1 sm:text-sm">
            Claude Code Remote Control
          </p>
        </div>
        <div className="flex items-center gap-2">
          <ThemeToggle />
          <ConnectionStatus />
        </div>
      </header>
      <ProjectGrid />
    </main>
  );
}
