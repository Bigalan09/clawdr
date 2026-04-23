"use client";

import { useCallback, useEffect, useState } from "react";
import type { AuthStatus } from "@/lib/api";
import { fetchAuthStatus, startAuthLogin, submitAuthCode } from "@/lib/api";

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

  return <LoginCard onAuthenticated={checkStatus} />;
}

function LoginCard({ onAuthenticated }: { onAuthenticated: () => void }) {
  const [oauthUrl, setOauthUrl] = useState<string | null>(null);
  const [code, setCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  async function handleLogin() {
    setLoading(true);
    setError(null);
    try {
      const res = await startAuthLogin();
      setOauthUrl(res.oauth_url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start login");
    } finally {
      setLoading(false);
    }
  }

  async function handleSubmitCode() {
    if (!code.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      const res = await submitAuthCode(code.trim());
      if (res.success) {
        setSuccess(true);
        setTimeout(onAuthenticated, 500);
      } else {
        setError(res.message);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to submit code");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <div className="w-full max-w-md rounded-2xl border border-border bg-surface-raised p-8">
        <div className="mb-6 text-center">
          <h1 className="text-2xl font-bold tracking-tight text-text-primary">
            ClawdR
          </h1>
          <p className="mt-1 text-sm text-text-muted">
            Claude Code Remote Control
          </p>
        </div>

        {success ? (
          <div className="rounded-xl bg-green-500/10 p-4 text-center">
            <p className="text-sm font-medium text-green-400">
              Authenticated successfully
            </p>
          </div>
        ) : !oauthUrl ? (
          <div className="space-y-4">
            <p className="text-center text-sm text-text-secondary">
              Sign in with your Claude account to start managing remote control
              sessions.
            </p>
            <button
              type="button"
              onClick={handleLogin}
              disabled={loading}
              className="w-full rounded-xl bg-blue-600 px-4 py-3 text-sm font-medium text-white transition-colors hover:bg-blue-500 disabled:opacity-50"
            >
              {loading ? "Preparing sign-in..." : "Sign in with Claude"}
            </button>
          </div>
        ) : (
          <div className="space-y-5">
            <div>
              <p className="mb-2 text-sm font-medium text-text-secondary">
                Step 1: Sign in
              </p>
              <a
                href={oauthUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="flex w-full items-center justify-center rounded-xl bg-blue-600 px-4 py-3 text-sm font-medium text-white transition-colors hover:bg-blue-500"
              >
                Open Claude sign-in
              </a>
            </div>

            <div>
              <p className="mb-2 text-sm font-medium text-text-secondary">
                Step 2: Paste the code from the browser
              </p>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") handleSubmitCode();
                  }}
                  placeholder="Paste authorization code..."
                  autoFocus
                  className="flex-1 rounded-xl border border-border bg-surface-overlay px-4 py-3 font-mono text-sm text-text-primary placeholder-text-muted outline-none focus:border-blue-500"
                />
                <button
                  type="button"
                  onClick={handleSubmitCode}
                  disabled={submitting || !code.trim()}
                  className="shrink-0 rounded-xl bg-blue-600 px-5 py-3 text-sm font-medium text-white transition-colors hover:bg-blue-500 disabled:opacity-50"
                >
                  {submitting ? "Verifying..." : "Submit"}
                </button>
              </div>
            </div>

            <p className="text-center text-xs text-text-muted">
              Do not reload the page between steps.
            </p>
            <button
              type="button"
              onClick={() => {
                setOauthUrl(null);
                setCode("");
                setError(null);
              }}
              className="w-full text-center text-xs text-text-muted transition-colors hover:text-text-secondary"
            >
              Start over
            </button>
          </div>
        )}

        {error && (
          <p className="mt-4 rounded-lg bg-red-500/10 px-3 py-2 text-center text-xs text-red-400">
            {error}
          </p>
        )}
      </div>
    </div>
  );
}
