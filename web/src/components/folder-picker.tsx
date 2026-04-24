"use client";

import { type FormEvent, useCallback, useEffect, useState } from "react";
import type { BrowseResponse } from "@/lib/api";
import { browsePath, createDir } from "@/lib/api";

export function FolderPicker({
  value,
  onChange,
}: {
  value: string;
  onChange: (path: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const [browse, setBrowse] = useState<BrowseResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [newName, setNewName] = useState("");
  const [createError, setCreateError] = useState<string | null>(null);
  const [submittingNew, setSubmittingNew] = useState(false);

  const load = useCallback(async (path: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await browsePath(path);
      setBrowse(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Browse failed");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (open && !browse) {
      load(value || "");
    }
  }, [open, browse, load, value]);

  function resetNewFolder() {
    setCreating(false);
    setNewName("");
    setCreateError(null);
  }

  function closePicker() {
    setOpen(false);
    setBrowse(null);
    resetNewFolder();
  }

  function selectDir(path: string) {
    onChange(path);
    closePicker();
  }

  async function submitNewFolder(e: FormEvent) {
    e.preventDefault();
    if (!browse || !newName.trim()) return;
    setSubmittingNew(true);
    setCreateError(null);
    try {
      const data = await createDir(browse.current, newName.trim());
      setBrowse(data);
      resetNewFolder();
    } catch (err) {
      setCreateError(err instanceof Error ? err.message : "Create failed");
    } finally {
      setSubmittingNew(false);
    }
  }

  if (!open) {
    const selected = value.trim().length > 0;
    return (
      <div className="flex gap-2">
        <div className="relative flex-1">
          {selected && (
            <i
              className="fa-solid fa-circle-check pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-sm text-emerald-500"
              aria-hidden="true"
            />
          )}
          <input
            type="text"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder="/home/user/projects/my-project"
            className={`w-full rounded-lg border border-border bg-surface-overlay py-2 font-mono text-sm text-text-primary placeholder-text-muted outline-none focus:border-border-hover ${
              selected ? "pl-9 pr-3" : "px-3"
            }`}
          />
        </div>
        <button
          type="button"
          onClick={() => setOpen(true)}
          className="shrink-0 rounded-lg border border-border bg-surface-overlay px-3 py-2 text-sm text-text-secondary transition-colors hover:text-text-primary"
        >
          <i className="fa-solid fa-folder-open mr-1.5" aria-hidden="true" />
          Browse
        </button>
      </div>
    );
  }

  const currentName = browse ? displayName(browse.current) : "";

  return (
    <div className="rounded-lg border border-border bg-surface-overlay">
      <div className="flex items-center gap-2 border-b border-border px-3 py-2.5">
        <i
          className="fa-solid fa-folder-open text-sm text-text-muted"
          aria-hidden="true"
        />
        <p className="flex-1 truncate font-mono text-xs text-text-secondary">
          {browse?.current ?? "Loading..."}
        </p>
        <button
          type="button"
          onClick={() => {
            if (creating) {
              resetNewFolder();
            } else {
              setCreating(true);
            }
          }}
          disabled={!browse}
          className="text-xs text-text-secondary transition-colors hover:text-text-primary disabled:opacity-40"
        >
          <i className="fa-solid fa-folder-plus mr-1" aria-hidden="true" />
          {creating ? "Discard" : "New folder"}
        </button>
        <button
          type="button"
          onClick={closePicker}
          className="text-xs text-text-muted hover:text-text-primary"
        >
          Cancel
        </button>
      </div>

      {error && <p className="px-3 py-2 text-xs text-red-400">{error}</p>}

      {creating && browse && (
        <form
          onSubmit={submitNewFolder}
          className="flex flex-col gap-2 border-b border-border bg-surface-raised/40 px-3 py-2.5"
        >
          <div className="flex gap-2">
            <input
              type="text"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="new-folder-name"
              autoFocus
              className="flex-1 rounded-md border border-border bg-surface-overlay px-2.5 py-1.5 font-mono text-sm text-text-primary placeholder-text-muted outline-none focus:border-border-hover"
            />
            <button
              type="submit"
              disabled={submittingNew || !newName.trim()}
              className="rounded-md bg-blue-600 px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {submittingNew ? "Creating..." : "Create"}
            </button>
          </div>
          {createError && (
            <p className="text-xs text-red-400">{createError}</p>
          )}
        </form>
      )}

      <div className="max-h-64 overflow-y-auto py-1">
        {browse?.parent && (
          <button
            type="button"
            onClick={() => load(browse.parent!)}
            className="flex w-full items-center gap-3 px-3 py-2.5 text-left text-sm text-text-secondary hover:bg-surface-raised"
          >
            <i
              className="fa-solid fa-arrow-turn-up w-4 text-text-muted"
              aria-hidden="true"
            />
            <span>Up one level</span>
          </button>
        )}
        {loading && !browse && (
          <p className="px-3 py-4 text-center text-xs text-text-muted">
            Loading...
          </p>
        )}
        {browse?.entries.map((entry) => (
          <button
            type="button"
            key={entry.path}
            onClick={() => load(entry.path)}
            className="flex w-full items-center gap-3 px-3 py-2.5 text-left text-sm text-text-primary hover:bg-surface-raised"
          >
            <i
              className="fa-solid fa-folder w-4 text-amber-400/80"
              aria-hidden="true"
            />
            <span className="truncate">{entry.name}</span>
          </button>
        ))}
        {browse && browse.entries.length === 0 && !creating && (
          <p className="px-3 py-4 text-center text-xs text-text-muted">
            No subdirectories
          </p>
        )}
      </div>

      {browse && (
        <div className="border-t border-border bg-surface-raised/30 px-3 py-3">
          <button
            type="button"
            onClick={() => selectDir(browse.current)}
            className="flex w-full items-center justify-center gap-2 rounded-md bg-blue-600 px-3 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-blue-500"
          >
            <i className="fa-solid fa-circle-check" aria-hidden="true" />
            <span>
              Select this folder
              {currentName && (
                <span className="ml-1.5 font-mono font-normal opacity-90">
                  ({currentName})
                </span>
              )}
            </span>
          </button>
        </div>
      )}
    </div>
  );
}

function displayName(path: string): string {
  const trimmed = path.replace(/\/+$/, "");
  const idx = trimmed.lastIndexOf("/");
  if (idx < 0) return trimmed;
  const tail = trimmed.slice(idx + 1);
  return tail || trimmed;
}
