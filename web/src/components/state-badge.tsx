type SessionState = "stopped" | "starting" | "running" | "crashed";

const config: Record<
  SessionState,
  { label: string; dot: string; bg: string; text: string }
> = {
  stopped: {
    label: "Stopped",
    dot: "bg-neutral-400",
    bg: "bg-neutral-500/10",
    text: "text-neutral-400",
  },
  starting: {
    label: "Starting",
    dot: "bg-yellow-400 animate-pulse",
    bg: "bg-yellow-500/10",
    text: "text-yellow-600 dark:text-yellow-400",
  },
  running: {
    label: "Running",
    dot: "bg-green-400",
    bg: "bg-green-500/10",
    text: "text-green-600 dark:text-green-400",
  },
  crashed: {
    label: "Crashed",
    dot: "bg-red-400",
    bg: "bg-red-500/10",
    text: "text-red-600 dark:text-red-400",
  },
};

export function StateBadge({ state }: { state: SessionState }) {
  const c = config[state];
  return (
    <span
      className={`inline-flex shrink-0 items-center gap-1.5 rounded-full px-2 py-0.5 text-[10px] font-medium sm:px-2.5 sm:py-1 sm:text-xs ${c.bg} ${c.text}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${c.dot}`} />
      {c.label}
    </span>
  );
}
