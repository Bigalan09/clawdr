"use client";

import { useEffect, useState } from "react";
import { QRCodeSVG } from "qrcode.react";
import type { ProjectView } from "@/lib/api";
import { fetchSessionUrl } from "@/lib/api";

export function SessionUrl({ project }: { project: ProjectView }) {
  const [url, setUrl] = useState<string | null>(project.session_url ?? null);
  const [copied, setCopied] = useState(false);
  const [showQr, setShowQr] = useState(false);

  useEffect(() => {
    if (project.session_url) {
      setUrl(project.session_url);
      return;
    }
    if (project.session_state !== "running") {
      setUrl(null);
      return;
    }
    let cancelled = false;
    fetchSessionUrl(project.id).then((u) => {
      if (!cancelled) setUrl(u);
    });
    return () => {
      cancelled = true;
    };
  }, [project.id, project.session_state, project.session_url]);

  if (!url || project.session_state !== "running") return null;

  async function handleCopy() {
    if (!url) return;
    await navigator.clipboard.writeText(url);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-1.5 sm:gap-2">
        <a
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          className="min-w-0 flex-1 truncate rounded-md bg-surface-overlay px-2 py-1.5 font-mono text-[10px] text-blue-500 hover:text-blue-400 sm:px-2.5 sm:text-xs"
        >
          {url}
        </a>
        <button
          onClick={handleCopy}
          className="shrink-0 rounded-md bg-surface-overlay px-2 py-1.5 text-[10px] text-text-muted transition-colors hover:text-text-primary sm:text-xs"
        >
          {copied ? "Copied" : "Copy"}
        </button>
        <button
          onClick={() => setShowQr(!showQr)}
          className="shrink-0 rounded-md bg-surface-overlay px-2 py-1.5 text-[10px] text-text-muted transition-colors hover:text-text-primary sm:text-xs"
        >
          QR
        </button>
      </div>

      {showQr && (
        <div className="flex justify-center rounded-lg bg-white p-3">
          <QRCodeSVG value={url} size={140} />
        </div>
      )}
    </div>
  );
}
