"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { LogEntry } from "@/lib/api";
import { fetchAuthLogs } from "@/lib/api";

export function DevConsole() {
  const [open, setOpen] = useState(false);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);
  const sinceRef = useRef("");

  const poll = useCallback(async () => {
    const entries = await fetchAuthLogs(sinceRef.current);
    if (entries.length > 0) {
      setLogs((prev) => {
        const combined = [...prev, ...entries].slice(-200);
        sinceRef.current = combined[combined.length - 1].ts;
        return combined;
      });
    }
  }, []);

  useEffect(() => {
    if (!open) return;
    poll();
    const id = setInterval(poll, 2000);
    return () => clearInterval(id);
  }, [open, poll]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  function copyLogs() {
    const text = logs
      .map(
        (e) =>
          `${new Date(e.ts).toLocaleTimeString()} [${e.level}] ${e.msg}`,
      )
      .join("\n");
    navigator.clipboard.writeText(text);
  }

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="fixed bottom-4 right-4 z-50 flex h-10 w-10 items-center justify-center rounded-full border border-border bg-surface-raised text-text-muted shadow-lg transition-colors hover:text-text-primary"
        title="Dev Console"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="h-5 w-5"
        >
          <polyline points="4 17 10 11 4 5" />
          <line x1="12" y1="19" x2="20" y2="19" />
        </svg>
      </button>

      {open && (
        <div className="fixed bottom-0 right-0 z-40 flex w-full flex-col border-t border-border bg-surface-base sm:bottom-4 sm:right-4 sm:w-[520px] sm:rounded-xl sm:border"
          style={{ height: "320px" }}
        >
          <div className="flex shrink-0 items-center justify-between border-b border-border px-3 py-2">
            <span className="text-xs font-medium text-text-secondary">
              Dev Console
            </span>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={copyLogs}
                className="text-xs text-text-muted hover:text-text-secondary"
                title="Copy all logs"
              >
                Copy
              </button>
              <button
                type="button"
                onClick={() => {
                  setLogs([]);
                  sinceRef.current = "";
                }}
                className="text-xs text-text-muted hover:text-text-secondary"
              >
                Clear
              </button>
              <button
                type="button"
                onClick={() => setOpen(false)}
                className="text-xs text-text-muted hover:text-text-secondary"
              >
                Close
              </button>
            </div>
          </div>
          <div
            ref={scrollRef}
            className="min-h-0 flex-1 overflow-y-auto p-2 font-mono text-xs scrollbar-thin"
          >
            {logs.length === 0 && (
              <p className="py-4 text-center text-text-muted">
                No log entries yet
              </p>
            )}
            {logs.map((entry, i) => (
              <div
                key={`${entry.ts}-${i}`}
                className="flex gap-2 py-0.5"
                style={{ overflowWrap: "anywhere" }}
              >
                <span className="shrink-0 text-text-muted">
                  {new Date(entry.ts).toLocaleTimeString()}
                </span>
                <span
                  className={
                    entry.level === "error"
                      ? "break-all text-red-400"
                      : entry.level === "warning"
                        ? "break-all text-yellow-400"
                        : "break-all text-text-secondary"
                  }
                >
                  {entry.msg}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </>
  );
}
