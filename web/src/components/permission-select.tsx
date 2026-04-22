import { PERMISSION_MODES, type PermissionMode } from "@/lib/api";

export function PermissionSelect({
  value,
  onChange,
  className,
}: {
  value: PermissionMode;
  onChange: (mode: PermissionMode) => void;
  className?: string;
}) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value as PermissionMode)}
      className={`rounded-lg border border-border bg-surface-overlay px-3 py-2 text-sm text-text-primary outline-none focus:border-border-hover ${className ?? ""}`}
    >
      {PERMISSION_MODES.map((m) => (
        <option key={m.value} value={m.value}>
          {m.label}
        </option>
      ))}
    </select>
  );
}
