"use client";

import { useCallback, useEffect, useState } from "react";
import type { AuthStatus } from "@/lib/api";
import { fetchAuthStatus } from "@/lib/api";

const DOCKER_CMD = "docker exec -it clawdr claude auth login";

export function AuthGate({ children }: { children: React.ReactNode }) {
  const [status, setStatus] = useState<AuthStatus | null>(null);
  const [checking, setChecking] = useState(true);

  const checkStatus = useCallback(async () => {
    try {
      const s = await fetchAuthStatus();
      setStatus(s);
    } catch {
      setStatus({ logged_in: false, auth_method: "error", email: null });
    } finally {
      setChecking(false);
    }
  }, []);

  useEffect(() => {
    checkStatus();
  }, [checkStatus]);

  // Poll for auth status every 5s while not logged in.
  useEffect(() => {
    if (status?.logged_in) return;
    const id = setInterval(checkStatus, 5000);
    return () => clearInterval(id);
  }, [status?.logged_in, checkStatus]);

  if (checking) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-sm text-text-muted">Checking authentication...</p>
      </div>
    );
  }

  if (status?.logged_in) {
    return <>{children}</>;
  }

  return <LoginInstructions />;
}

function LoginInstructions() {
  const [copied, setCopied] = useState(false);

  function handleCopy() {
    navigator.clipboard.writeText(DOCKER_CMD);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <div className="w-full max-w-lg rounded-2xl border border-border bg-surface-raised p-8">
        <div className="mb-6 text-center">
          <h1 className="text-2xl font-bold tracking-tight text-text-primary">
            ClawdR
          </h1>
          <p className="mt-1 text-sm text-text-muted">
            Claude Code Remote Control
          </p>
        </div>

        <div className="rounded-xl border border-yellow-500/30 bg-yellow-500/5 p-4">
          <p className="text-sm font-medium text-yellow-400">
            Not authenticated
          </p>
          <p className="mt-2 text-sm text-text-secondary">
            Run the following command in your terminal to sign in:
          </p>

          <div className="mt-3 flex items-center gap-2">
            <code className="flex-1 overflow-x-auto rounded-lg bg-surface-base px-4 py-3 font-mono text-sm text-text-primary">
              {DOCKER_CMD}
            </code>
            <button
              type="button"
              onClick={handleCopy}
              className="shrink-0 rounded-lg border border-border bg-surface-overlay px-3 py-3 text-xs text-text-muted transition-colors hover:text-text-primary"
              title="Copy command"
            >
              {copied ? "Copied!" : "Copy"}
            </button>
          </div>

          <p className="mt-4 text-xs text-text-muted">
            This will open an interactive login session inside the container.
            Follow the prompts to complete OAuth sign-in. This page will
            automatically detect when you&apos;re logged in.
          </p>
        </div>
      </div>
    </div>
  );
}
