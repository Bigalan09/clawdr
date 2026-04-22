"use client";

import { useAppStore } from "@/lib/store";

const labels = {
  connected: "Live",
  connecting: "...",
  disconnected: "Offline",
} as const;

const dotColors = {
  connected: "bg-green-400",
  connecting: "bg-yellow-400 animate-pulse",
  disconnected: "bg-red-400",
} as const;

export function ConnectionStatus() {
  const status = useAppStore((s) => s.connectionStatus);

  return (
    <div className="flex items-center gap-1.5 rounded-full border border-border bg-surface-raised px-2.5 py-1 sm:gap-2 sm:px-3 sm:py-1.5">
      <span className={`h-1.5 w-1.5 rounded-full sm:h-2 sm:w-2 ${dotColors[status]}`} />
      <span className="text-[10px] font-medium text-text-secondary sm:text-xs">
        {labels[status]}
      </span>
    </div>
  );
}
