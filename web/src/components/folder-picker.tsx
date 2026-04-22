"use client";

import { useCallback, useEffect, useState } from "react";
import type { BrowseResponse } from "@/lib/api";
import { browsePath } from "@/lib/api";

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
      load(value || "~");
    }
  }, [open, browse, load, value]);

  function selectDir(path: string) {
    onChange(path);
    setOpen(false);
    setBrowse(null);
  }

  if (!open) {
    return (
      <div className="flex gap-2">
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="/home/user/projects/my-project"
          className="flex-1 rounded-lg border border-border bg-surface-overlay px-3 py-2 font-mono text-sm text-text-primary placeholder-text-muted outline-none focus:border-border-hover"
        />
        <button
          type="button"
          onClick={() => setOpen(true)}
          className="shrink-0 rounded-lg border border-border bg-surface-overlay px-3 py-2 text-sm text-text-secondary transition-colors hover:text-text-primary"
        >
          Browse
        </button>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-border bg-surface-overlay">
      <div className="flex items-center gap-2 border-b border-border px-3 py-2">
        <p className="flex-1 truncate font-mono text-xs text-text-secondary">
          {browse?.current ?? "Loading..."}
        </p>
        <button
          type="button"
          onClick={() => {
            setOpen(false);
            setBrowse(null);
          }}
          className="text-xs text-text-muted hover:text-text-primary"
        >
          Cancel
        </button>
      </div>

      {error && (
        <p className="px-3 py-2 text-xs text-red-400">{error}</p>
      )}

      <div className="max-h-48 overflow-y-auto">
        {browse?.parent && (
          <button
            type="button"
            onClick={() => load(browse.parent!)}
            className="flex w-full items-center gap-2 px-3 py-1.5 text-left text-sm text-text-secondary hover:bg-surface-raised"
          >
            <span className="text-text-muted">..</span>
          </button>
        )}
        {loading && !browse && (
          <p className="px-3 py-3 text-center text-xs text-text-muted">
            Loading...
          </p>
        )}
        {browse?.entries.map((entry) => (
          <button
            type="button"
            key={entry.path}
            onClick={() => load(entry.path)}
            className="flex w-full items-center gap-2 px-3 py-1.5 text-left text-sm text-text-primary hover:bg-surface-raised"
          >
            <span className="truncate">{entry.name}</span>
          </button>
        ))}
        {browse && browse.entries.length === 0 && (
          <p className="px-3 py-3 text-center text-xs text-text-muted">
            No subdirectories
          </p>
        )}
      </div>

      {browse && (
        <div className="border-t border-border px-3 py-2">
          <button
            type="button"
            onClick={() => selectDir(browse.current)}
            className="w-full rounded-md bg-blue-600 px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-blue-500"
          >
            Select this folder
          </button>
        </div>
      )}
    </div>
  );
}
