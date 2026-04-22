"use client";

import { useState } from "react";
import { useAppStore } from "@/lib/store";
import { AddProjectModal } from "./add-project-modal";
import { ProjectCard } from "./project-card";

const PAGE_SIZE = 6;

export function ProjectGrid() {
  const projects = useAppStore((s) => s.projects);
  const error = useAppStore((s) => s.error);
  const [showAdd, setShowAdd] = useState(false);
  const [page, setPage] = useState(0);

  if (error) {
    return (
      <div className="rounded-xl border border-red-500/30 bg-red-500/5 p-6 text-center text-sm text-red-400">
        {error}
      </div>
    );
  }

  const totalPages = Math.max(1, Math.ceil(projects.length / PAGE_SIZE));
  const safeP = Math.min(page, totalPages - 1);
  const slice = projects.slice(safeP * PAGE_SIZE, (safeP + 1) * PAGE_SIZE);

  return (
    <>
      <div className="grid gap-3 sm:gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {slice.map((p) => (
          <ProjectCard key={p.id} project={p} />
        ))}

        <button
          onClick={() => setShowAdd(true)}
          className="flex min-h-[120px] items-center justify-center rounded-xl border border-dashed border-border bg-surface-raised/30 text-sm text-text-muted transition-colors hover:border-border-hover hover:text-text-secondary sm:min-h-[140px]"
        >
          + Add Project
        </button>
      </div>

      {totalPages > 1 && (
        <div className="mt-4 flex items-center justify-center gap-2 sm:mt-6">
          <button
            onClick={() => setPage((p) => Math.max(0, p - 1))}
            disabled={safeP === 0}
            className="rounded-lg border border-border bg-surface-raised px-3 py-1.5 text-xs font-medium text-text-secondary transition-colors hover:bg-surface-overlay disabled:opacity-30"
          >
            Prev
          </button>
          <span className="text-xs text-text-muted">
            {safeP + 1} / {totalPages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
            disabled={safeP >= totalPages - 1}
            className="rounded-lg border border-border bg-surface-raised px-3 py-1.5 text-xs font-medium text-text-secondary transition-colors hover:bg-surface-overlay disabled:opacity-30"
          >
            Next
          </button>
        </div>
      )}

      {showAdd && <AddProjectModal onClose={() => setShowAdd(false)} />}
    </>
  );
}
