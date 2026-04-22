"use client";

import { type FormEvent, useState } from "react";
import type { PermissionMode } from "@/lib/api";
import { addProject } from "@/lib/api";
import { useAppStore } from "@/lib/store";
import { FolderPicker } from "./folder-picker";
import { PermissionSelect } from "./permission-select";

export function AddProjectModal({ onClose }: { onClose: () => void }) {
  const [name, setName] = useState("");
  const [path, setPath] = useState("");
  const [permissionMode, setPermissionMode] =
    useState<PermissionMode>("default");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const loadProjects = useAppStore((s) => s.loadProjects);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!name.trim() || !path.trim()) return;

    setSubmitting(true);
    setError(null);
    try {
      await addProject(name.trim(), path.trim(), permissionMode);
      await loadProjects();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add project");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-black/60 backdrop-blur-sm sm:items-center"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-md rounded-t-xl border border-border bg-surface-raised p-5 sm:rounded-xl sm:p-6"
      >
        <h2 className="mb-4 text-lg font-semibold text-text-primary">
          Add Project
        </h2>

        <label className="mb-1 block text-sm text-text-secondary">Name</label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="My Project"
          autoFocus
          className="mb-4 w-full rounded-lg border border-border bg-surface-overlay px-3 py-2 text-sm text-text-primary placeholder-text-muted outline-none focus:border-border-hover"
        />

        <label className="mb-1 block text-sm text-text-secondary">Path</label>
        <div className="mb-4">
          <FolderPicker value={path} onChange={setPath} />
        </div>

        <label className="mb-1 block text-sm text-text-secondary">
          Permission Mode
        </label>
        <PermissionSelect
          value={permissionMode}
          onChange={setPermissionMode}
          className="mb-4 w-full"
        />

        {error && <p className="mb-3 text-xs text-red-400">{error}</p>}

        <div className="flex gap-3">
          <button
            type="button"
            onClick={onClose}
            className="flex-1 rounded-lg border border-border px-4 py-2.5 text-sm font-medium text-text-secondary transition-colors hover:bg-surface-overlay"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={submitting || !name.trim() || !path.trim()}
            className="flex-1 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {submitting ? "Adding..." : "Add Project"}
          </button>
        </div>
      </form>
    </div>
  );
}
