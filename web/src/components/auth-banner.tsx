"use client";

import { useCallback, useEffect, useState } from "react";
import type { AuthStatus } from "@/lib/api";
import { fetchAuthStatus, startAuthLogin, submitAuthCode } from "@/lib/api";

export function AuthBanner() {
  const [status, setStatus] = useState<AuthStatus | null>(null);
  const [oauthUrl, setOauthUrl] = useState<string | null>(null);
  const [code, setCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const checkStatus = useCallback(async () => {
    try {
      const s = await fetchAuthStatus();
      setStatus(s);
      if (s.logged_in) {
        setOauthUrl(null);
        setCode("");
      }
    } catch {
      // Silently fail - banner just won't show
    }
  }, []);

  useEffect(() => {
    checkStatus();
  }, [checkStatus]);

  if (status === null || status.logged_in) return null;

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
        await checkStatus();
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
    <div className="mb-4 rounded-xl border border-yellow-500/30 bg-yellow-500/5 p-4">
      <p className="text-sm font-medium text-yellow-400">
        Claude Code not authenticated
      </p>

      {!oauthUrl && (
        <div className="mt-2 flex items-center gap-3">
          <p className="text-xs text-text-muted">
            Sign in to start remote control sessions.
          </p>
          <button
            type="button"
            onClick={handleLogin}
            disabled={loading}
            className="shrink-0 rounded-lg bg-yellow-600 px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-yellow-500 disabled:opacity-50"
          >
            {loading ? "Starting..." : "Sign in"}
          </button>
        </div>
      )}

      {oauthUrl && (
        <div className="mt-2 space-y-3">
          <div className="flex items-center gap-2">
            <span className="text-xs text-text-muted">Step 1:</span>
            <a
              href={oauthUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-block rounded-md bg-yellow-600 px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-yellow-500"
            >
              Open sign-in page
            </a>
          </div>
          <div>
            <p className="mb-1.5 text-xs text-text-muted">
              Step 2: Paste the code from the browser here
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
                className="flex-1 rounded-lg border border-border bg-surface-overlay px-3 py-2 font-mono text-sm text-text-primary placeholder-text-muted outline-none focus:border-border-hover"
              />
              <button
                type="button"
                onClick={handleSubmitCode}
                disabled={submitting || !code.trim()}
                className="shrink-0 rounded-lg bg-yellow-600 px-4 py-2 text-xs font-medium text-white transition-colors hover:bg-yellow-500 disabled:opacity-50"
              >
                {submitting ? "Verifying..." : "Submit"}
              </button>
            </div>
          </div>
        </div>
      )}

      {error && <p className="mt-2 text-xs text-red-400">{error}</p>}
    </div>
  );
}
