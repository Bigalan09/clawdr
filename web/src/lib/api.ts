const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

export const PERMISSION_MODES = [
  { value: "default", label: "Default" },
  { value: "auto", label: "Auto" },
  { value: "bypassPermissions", label: "Bypass Permissions" },
  { value: "plan", label: "Plan" },
  { value: "dontAsk", label: "Don't Ask" },
  { value: "acceptEdits", label: "Accept Edits" },
] as const;

export type PermissionMode = (typeof PERMISSION_MODES)[number]["value"];

export interface ProjectView {
  id: string;
  name: string;
  path: string;
  source: string;
  session_state: "stopped" | "starting" | "running" | "crashed";
  started_at: string | null;
  permission_mode: PermissionMode;
  session_url?: string | null;
}

interface ProjectListResponse {
  projects: ProjectView[];
}

interface SessionActionResponse {
  project_id: string;
  session_state: string;
}

interface SessionUrlResponse {
  project_id: string;
  url: string | null;
}

export async function fetchProjects(): Promise<ProjectView[]> {
  const res = await fetch(`${API_BASE}/projects`);
  if (!res.ok) throw new Error(`Failed to fetch projects: ${res.status}`);
  const data: ProjectListResponse = await res.json();
  return data.projects;
}

export async function startSession(
  projectId: string,
  permissionMode?: string,
): Promise<SessionActionResponse> {
  const res = await fetch(`${API_BASE}/projects/${projectId}/session`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(
      permissionMode ? { permission_mode: permissionMode } : {},
    ),
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(detail.detail ?? `Failed: ${res.status}`);
  }
  return res.json();
}

export async function stopSession(
  projectId: string,
): Promise<SessionActionResponse> {
  const res = await fetch(`${API_BASE}/projects/${projectId}/session`, {
    method: "DELETE",
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(detail.detail ?? `Failed: ${res.status}`);
  }
  return res.json();
}

export async function fetchSessionUrl(
  projectId: string,
): Promise<string | null> {
  const res = await fetch(`${API_BASE}/projects/${projectId}/session/url`);
  if (!res.ok) return null;
  const data: SessionUrlResponse = await res.json();
  return data.url;
}

export async function addProject(
  name: string,
  path: string,
  permissionMode: string = "default",
): Promise<ProjectView> {
  const res = await fetch(`${API_BASE}/projects`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, path, permission_mode: permissionMode }),
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(detail.detail ?? `Failed: ${res.status}`);
  }
  return res.json();
}

export interface DirEntry {
  name: string;
  path: string;
  is_dir: boolean;
}

export interface BrowseResponse {
  current: string;
  parent: string | null;
  entries: DirEntry[];
}

export async function browsePath(
  path: string = "",
): Promise<BrowseResponse> {
  const params = path ? `?path=${encodeURIComponent(path)}` : "";
  const res = await fetch(
    `${API_BASE}/browse${params}`,
  );
  if (!res.ok) {
    const detail = await res.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(detail.detail ?? `Failed: ${res.status}`);
  }
  return res.json();
}

export async function removeProject(projectId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/projects/${projectId}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(detail.detail ?? `Failed: ${res.status}`);
  }
}
