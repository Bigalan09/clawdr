"use client";

import { useState } from "react";
import type { PermissionMode, ProjectView } from "@/lib/api";
import { PERMISSION_MODES, removeProject, startSession, stopSession } from "@/lib/api";
import { useAppStore } from "@/lib/store";
import { SessionTimer } from "./session-timer";
import { SessionUrl } from "./session-url";
import { StateBadge } from "./state-badge";

export function ProjectCard({ project }: { project: ProjectView }) {
  const [loading, setLoading] = useState(false);
  const [removing, setRemoving] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [startPerm, setStartPerm] = useState<PermissionMode>(
    project.permission_mode,
  );
  const updateProjectState = useAppStore((s) => s.updateProjectState);
  const loadProjects = useAppStore((s) => s.loadProjects);

  const isActive =
    project.session_state === "starting" ||
    project.session_state === "running";

  const permLabel = PERMISSION_MODES.find(
    (m) => m.value === project.permission_mode,
  )?.label;

  async function handleToggle() {
    setLoading(true);
    setActionError(null);
    try {
      if (isActive) {
        await stopSession(project.id);
        updateProjectState(project.id, "stopped", {
          startedAt: null,
          url: null,
        });
      } else {
        const res = await startSession(project.id, startPerm);
        updateProjectState(
          project.id,
          res.session_state as ProjectView["session_state"],
        );
      }
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Action failed");
    } finally {
      setLoading(false);
    }
  }

  async function handleRemove() {
    if (isActive) {
      setActionError("Stop the session before removing");
      return;
    }
    setRemoving(true);
    setActionError(null);
    try {
      await removeProject(project.id);
      await loadProjects();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Remove failed");
      setRemoving(false);
    }
  }

  return (
    <div className="flex flex-col gap-2.5 rounded-xl border border-border bg-surface-raised p-4 transition-colors hover:border-border-hover sm:gap-3 sm:p-5">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <h2 className="text-base font-semibold text-text-primary sm:text-lg">
            {project.name}
          </h2>
          <p className="mt-0.5 break-all font-mono text-[10px] text-text-muted sm:text-xs">
            {project.path}
          </p>
          <p className="mt-0.5 text-[10px] text-text-muted sm:text-xs">
            {permLabel ?? project.permission_mode}
          </p>
        </div>
        <StateBadge state={project.session_state} />
      </div>

      {isActive && project.started_at && (
        <SessionTimer startedAt={project.started_at} />
      )}

      <SessionUrl project={project} />

      {actionError && <p className="text-xs text-red-400">{actionError}</p>}

      {/* Permission mode selector — only shown when stopped */}
      {!isActive && (
        <select
          value={startPerm}
          onChange={(e) => setStartPerm(e.target.value as PermissionMode)}
          className="rounded-lg border border-border bg-surface-overlay px-2 py-1.5 text-xs text-text-secondary outline-none focus:border-border-hover"
        >
          {PERMISSION_MODES.map((m) => (
            <option key={m.value} value={m.value}>
              {m.label}
            </option>
          ))}
        </select>
      )}

      <div className="mt-auto flex gap-2">
        <button
          onClick={handleToggle}
          disabled={loading || removing}
          className={`flex-1 rounded-lg px-3 py-2 text-sm font-medium transition-all disabled:cursor-not-allowed disabled:opacity-50 sm:px-4 sm:py-2.5 ${
            isActive
              ? "bg-red-500/10 text-red-400 hover:bg-red-500/20 active:bg-red-500/30"
              : "bg-green-500/10 text-green-400 hover:bg-green-500/20 active:bg-green-500/30"
          }`}
        >
          {loading
            ? isActive
              ? "Stopping..."
              : "Starting..."
            : isActive
              ? "Stop"
              : "Start"}
        </button>
        <button
          onClick={handleRemove}
          disabled={loading || removing || isActive}
          title={isActive ? "Stop session first" : "Remove project"}
          className="rounded-lg bg-surface-overlay px-2.5 py-2 text-sm text-text-muted transition-all hover:text-red-400 disabled:cursor-not-allowed disabled:opacity-30 sm:px-3 sm:py-2.5"
        >
          {removing ? "..." : "Remove"}
        </button>
      </div>
    </div>
  );
}
