"use client";

import { useCallback, useEffect, useState } from "react";
import type { AuthStatus } from "@/lib/api";
import { fetchAuthStatus, startAuthLogin } from "@/lib/api";

export function AuthBanner() {
  const [status, setStatus] = useState<AuthStatus | null>(null);
  const [oauthUrl, setOauthUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const checkStatus = useCallback(async () => {
    try {
      const s = await fetchAuthStatus();
      setStatus(s);
      if (s.logged_in) {
        setOauthUrl(null);
      }
    } catch {
      // Silently fail - banner just won't show
    }
  }, []);

  useEffect(() => {
    checkStatus();
  }, [checkStatus]);

  // Poll auth status while waiting for OAuth completion
  useEffect(() => {
    if (!oauthUrl) return;
    const interval = setInterval(checkStatus, 5000);
    return () => clearInterval(interval);
  }, [oauthUrl, checkStatus]);

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

  return (
    <div className="mb-4 rounded-xl border border-yellow-500/30 bg-yellow-500/5 p-4">
      <div className="flex items-start gap-3">
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium text-yellow-400">
            Claude Code not authenticated
          </p>
          {!oauthUrl && (
            <p className="mt-1 text-xs text-text-muted">
              Sign in to start remote control sessions.
            </p>
          )}
          {oauthUrl && (
            <div className="mt-2">
              <p className="text-xs text-text-muted">
                Complete sign-in in your browser, then this banner will
                disappear automatically.
              </p>
              <a
                href={oauthUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-2 inline-block rounded-md bg-yellow-600 px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-yellow-500"
              >
                Open sign-in page
              </a>
            </div>
          )}
          {error && <p className="mt-1 text-xs text-red-400">{error}</p>}
        </div>
        {!oauthUrl && (
          <button
            type="button"
            onClick={handleLogin}
            disabled={loading}
            className="shrink-0 rounded-lg bg-yellow-600 px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-yellow-500 disabled:opacity-50"
          >
            {loading ? "Starting..." : "Sign in"}
          </button>
        )}
      </div>
    </div>
  );
}
