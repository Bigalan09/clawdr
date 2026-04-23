"""Claude Code authentication status and OAuth flow endpoints."""

from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import logging
import os
import secrets
import urllib.request
from collections import deque
from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter(tags=["auth"])

logger = logging.getLogger(__name__)

# ── Ring-buffer log for the frontend dev console ──────────────────────
_MAX_LOG_ENTRIES = 200
_log_buffer: deque[dict[str, str]] = deque(maxlen=_MAX_LOG_ENTRIES)

# Claude Code OAuth constants (from the CLI source).
_CLIENT_ID = "9d1c250a-e61b-44d9-88ed-5944d1962f5e"
_REDIRECT_URI = "https://platform.claude.com/oauth/code/callback"
_AUTHORIZE_URL = "https://claude.ai/oauth/authorize"
_TOKEN_URL = "https://claude.ai/oauth/token"  # noqa: S105
_FULL_SCOPES = (
    "org:create_api_key "
    "user:profile "
    "user:inference "
    "user:sessions:claude_code "
    "user:mcp_servers "
    "user:file_upload"
)
_CREDENTIALS_PATH = os.path.expanduser("~/.claude/.credentials.json")


def _log(level: str, msg: str) -> None:
    """Log to both Python logger and the ring buffer."""
    getattr(logger, level, logger.info)(msg)
    from datetime import UTC, datetime

    _log_buffer.append({"ts": datetime.now(UTC).isoformat(), "level": level, "msg": msg})


class AuthStatusResponse(BaseModel):
    """Response for GET /api/auth/status."""

    logged_in: bool
    auth_method: str
    email: str | None = None


class AuthLoginResponse(BaseModel):
    """Response for POST /api/auth/login."""

    oauth_url: str


class AuthCallbackRequest(BaseModel):
    """Request body for POST /api/auth/callback."""

    code: str


class AuthCallbackResponse(BaseModel):
    """Response for POST /api/auth/callback."""

    success: bool
    message: str


class LogEntry(BaseModel):
    """A single log entry."""

    ts: str
    level: str
    msg: str


async def _run_claude_command(*args: str, deadline: float = 15) -> str:
    """Run a claude CLI command and return combined stdout+stderr."""
    proc = await asyncio.create_subprocess_exec(
        "claude",
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    try:
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=deadline)
    except TimeoutError as exc:
        proc.kill()
        await proc.wait()
        msg = "claude command timed out"
        raise RuntimeError(msg) from exc
    return stdout.decode("utf-8", errors="replace")


@router.get("/auth/status", response_model=AuthStatusResponse)
async def auth_status() -> AuthStatusResponse:
    """Check whether the Claude CLI is authenticated."""
    try:
        output = await _run_claude_command("auth", "status", "--json")
    except (FileNotFoundError, RuntimeError) as exc:
        _log("error", f"Failed to check auth status: {exc}")
        return AuthStatusResponse(logged_in=False, auth_method="error")

    try:
        data = json.loads(output.strip())
    except json.JSONDecodeError:
        _log("warning", f"Unexpected auth status output: {output[:200]}")
        return AuthStatusResponse(logged_in=False, auth_method="unknown")

    email: str | None = None
    if data.get("loggedIn"):
        try:
            config_output = await _run_claude_command(
                "config",
                "get",
                "--json",
                "oauthAccount",
            )
            config = json.loads(config_output.strip())
            email = config.get("emailAddress")
        except (FileNotFoundError, RuntimeError, json.JSONDecodeError):
            pass

    return AuthStatusResponse(
        logged_in=data.get("loggedIn", False),
        auth_method=data.get("authMethod", "unknown"),
        email=email,
    )


# ── PKCE OAuth flow (no CLI needed) ──────────────────────────────────
_pkce_code_verifier: str | None = None


def _generate_pkce() -> tuple[str, str]:
    """Generate a PKCE code_verifier and code_challenge."""
    verifier = secrets.token_urlsafe(64)[:128]
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return verifier, challenge


@router.post("/auth/login", response_model=AuthLoginResponse)
async def auth_login() -> AuthLoginResponse:
    """Generate an OAuth authorization URL with PKCE.

    We build the URL ourselves so we control the scopes (including RC)
    and hold onto the ``code_verifier`` for the token exchange.
    """
    global _pkce_code_verifier

    verifier, challenge = _generate_pkce()
    _pkce_code_verifier = verifier

    state = secrets.token_urlsafe(32)

    params = urlencode(
        {
            "code": "true",
            "client_id": _CLIENT_ID,
            "response_type": "code",
            "redirect_uri": _REDIRECT_URI,
            "scope": _FULL_SCOPES,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "state": state,
        }
    )
    url = f"{_AUTHORIZE_URL}?{params}"

    _log("info", f"Generated OAuth URL ({len(url)} chars), verifier stored")
    return AuthLoginResponse(oauth_url=url)


@router.post("/auth/callback", response_model=AuthCallbackResponse)
async def auth_callback(body: AuthCallbackRequest) -> AuthCallbackResponse:
    """Exchange the authorization code for tokens and store credentials."""
    global _pkce_code_verifier

    if _pkce_code_verifier is None:
        raise HTTPException(
            status_code=409,
            detail="No login flow in progress. Call POST /api/auth/login first.",
        )

    code = body.code.strip()
    verifier = _pkce_code_verifier
    _pkce_code_verifier = None

    _log("info", f"Exchanging auth code ({len(code)} chars) for tokens...")

    # Exchange authorization code for tokens.
    token_data = urlencode(
        {
            "grant_type": "authorization_code",
            "client_id": _CLIENT_ID,
            "code": code,
            "redirect_uri": _REDIRECT_URI,
            "code_verifier": verifier,
        }
    ).encode()

    req = urllib.request.Request(  # noqa: S310
        _TOKEN_URL,
        data=token_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )

    try:
        loop = asyncio.get_event_loop()
        response_body = await asyncio.wait_for(
            loop.run_in_executor(None, _do_token_request, req),
            timeout=30,
        )
        tokens = json.loads(response_body)
    except TimeoutError:
        _log("error", "Token exchange timed out")
        return AuthCallbackResponse(success=False, message="Token exchange timed out")
    except Exception as exc:
        _log("error", f"Token exchange failed: {exc}")
        return AuthCallbackResponse(success=False, message=f"Token exchange failed: {exc}")

    if "error" in tokens:
        _log("error", f"OAuth error: {tokens}")
        return AuthCallbackResponse(
            success=False,
            message=f"OAuth error: {tokens.get('error_description', tokens.get('error'))}",
        )

    _log("info", "Token exchange successful, writing credentials...")

    # Write credentials in the format Claude Code expects on Linux.
    credentials = {
        "claudeAiOauth": {
            "accessToken": tokens.get("access_token", ""),
            "refreshToken": tokens.get("refresh_token", ""),
            "expiresAt": _compute_expires_at(tokens.get("expires_in", 3600)),
            "scopes": _FULL_SCOPES.split(" "),
        }
    }

    try:
        os.makedirs(os.path.dirname(_CREDENTIALS_PATH), exist_ok=True)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _write_credentials_file, json.dumps(credentials, indent=2))
        _log("info", f"Credentials written to {_CREDENTIALS_PATH}")
    except OSError as exc:
        _log("error", f"Failed to write credentials: {exc}")
        return AuthCallbackResponse(success=False, message=f"Failed to write credentials: {exc}")

    return AuthCallbackResponse(success=True, message="Authentication successful")


def _write_credentials_file(content: str) -> None:
    """Write credentials to disk (runs in executor)."""
    import pathlib

    p = pathlib.Path(_CREDENTIALS_PATH)
    p.write_text(content)
    p.chmod(0o600)


def _do_token_request(req: urllib.request.Request) -> str:
    """Perform the token exchange HTTP request (runs in executor)."""
    import urllib.error

    try:
        with urllib.request.urlopen(req, timeout=25) as resp:  # noqa: S310
            result: str = resp.read().decode()
            return result
    except urllib.error.HTTPError as exc:
        body = exc.read().decode() if exc.fp else ""
        msg = f"HTTP {exc.code}: {body[:300]}"
        raise RuntimeError(msg) from exc


def _compute_expires_at(expires_in: int) -> int:
    """Convert expires_in seconds to a Unix timestamp in milliseconds."""
    import time

    return int((time.time() + expires_in) * 1000)


@router.get("/auth/logs", response_model=list[LogEntry])
async def auth_logs(since: str = Query(default="")) -> list[LogEntry]:
    """Return recent auth log entries for the frontend dev console."""
    entries = list(_log_buffer)
    if since:
        entries = [e for e in entries if e["ts"] > since]
    return [LogEntry(**e) for e in entries]
