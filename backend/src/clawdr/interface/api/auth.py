"""Claude Code authentication status and OAuth flow endpoints."""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import os
import pty
import re
from collections import deque

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter(tags=["auth"])

logger = logging.getLogger(__name__)

_OAUTH_URL_PATTERN = re.compile(r"https://claude\.com/cai/oauth/authorize\S+")
_ANSI_ESCAPE = re.compile(r"\x1b[\[\(][0-9;]*[a-zA-Z]|\x1b\][^\x07]*\x07|\r")

# ── Ring-buffer log for the frontend dev console ──────────────────────
_MAX_LOG_ENTRIES = 200
_log_buffer: deque[dict[str, str]] = deque(maxlen=_MAX_LOG_ENTRIES)


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


# ── PTY-based login state ────────────────────────────────────────────
_pty_master_fd: int | None = None
_pty_pid: int | None = None
_drain_task: asyncio.Task[None] | None = None
_pty_output: str = ""


def _cleanup_login() -> None:
    """Reset all login state."""
    global _pty_master_fd, _pty_pid, _drain_task, _pty_output
    if _drain_task and not _drain_task.done():
        _drain_task.cancel()
    if _pty_master_fd is not None:
        with contextlib.suppress(OSError):
            os.close(_pty_master_fd)
    _pty_master_fd = None
    _pty_pid = None
    _drain_task = None
    _pty_output = ""


async def _drain_pty(fd: int) -> None:
    """Keep reading PTY output in the background so the process doesn't block."""
    global _pty_output
    loop = asyncio.get_event_loop()
    while True:
        try:
            data = await loop.run_in_executor(None, os.read, fd, 4096)
            if not data:
                break
            text = data.decode("utf-8", errors="replace")
            _pty_output += text
        except OSError:
            break


@router.post("/auth/login", response_model=AuthLoginResponse)
async def auth_login() -> AuthLoginResponse:
    """Start the OAuth login flow using a real PTY.

    Forks a child process with ``claude auth login`` attached to a
    pseudo-terminal so the CLI enters interactive mode and shows the
    "Paste code here" prompt.
    """
    global _pty_master_fd, _pty_pid, _drain_task, _pty_output

    _cleanup_login()
    _pty_output = ""

    _log("info", "Starting claude auth login with PTY")

    try:
        pid, fd = pty.openpty()
    except OSError as exc:
        _log("error", f"Failed to open PTY: {exc}")
        raise HTTPException(status_code=500, detail=f"PTY allocation failed: {exc}") from exc

    child_pid = os.fork()
    if child_pid == 0:
        # ── Child process ──
        os.close(fd)  # close master in child
        os.setsid()
        os.dup2(pid, 0)  # stdin
        os.dup2(pid, 1)  # stdout
        os.dup2(pid, 2)  # stderr
        if pid > 2:
            os.close(pid)
        os.execvp("claude", ["claude", "auth", "login"])  # noqa: S606, S607
        os._exit(1)

    # ── Parent process ──
    os.close(pid)  # close slave in parent
    _pty_master_fd = fd
    _pty_pid = child_pid

    # Start background drain so the PTY buffer doesn't fill up.
    _drain_task = asyncio.create_task(_drain_pty(fd))

    # Wait for the OAuth URL to appear in output (max 30s).
    try:
        async with asyncio.timeout(30):
            while True:
                await asyncio.sleep(0.2)
                clean = _ANSI_ESCAPE.sub("", _pty_output)
                match = _OAUTH_URL_PATTERN.search(clean)
                if match:
                    url = match.group(0)
                    _log("info", f"Got OAuth URL: {url[:80]}...")
                    return AuthLoginResponse(oauth_url=url)
    except TimeoutError:
        _log("error", f"Timed out waiting for OAuth URL. Output so far: {_pty_output[:500]}")
        _cleanup_login()
        raise HTTPException(
            status_code=500,
            detail="Timed out waiting for OAuth URL",
        ) from None


@router.post("/auth/callback", response_model=AuthCallbackResponse)
async def auth_callback(body: AuthCallbackRequest) -> AuthCallbackResponse:
    """Feed the OAuth code back to the waiting ``claude auth login`` process."""
    global _pty_master_fd, _pty_pid

    if _pty_master_fd is None or _pty_pid is None:
        raise HTTPException(
            status_code=409,
            detail="No login process is waiting for a code. Call POST /api/auth/login first.",
        )

    code = body.code.strip()
    _log("info", f"Submitting auth code ({len(code)} chars) to login process (pid={_pty_pid})")

    try:
        os.write(_pty_master_fd, (code + "\r").encode())
    except OSError as exc:
        _log("error", f"Failed to write code to PTY: {exc}")
        _cleanup_login()
        raise HTTPException(status_code=500, detail=f"Failed to send code: {exc}") from exc

    _log("info", "Code written to PTY, waiting for process to finish...")

    # Wait for the child to exit.
    try:
        async with asyncio.timeout(30):
            loop = asyncio.get_event_loop()
            _, status = await loop.run_in_executor(None, os.waitpid, _pty_pid, 0)
            exit_code = os.WEXITSTATUS(status) if os.WIFEXITED(status) else -1
    except TimeoutError:
        _log("error", "Login process timed out after receiving code")
        import signal

        with contextlib.suppress(OSError):
            os.kill(_pty_pid, signal.SIGKILL)
        with contextlib.suppress(ChildProcessError, OSError):
            await asyncio.get_event_loop().run_in_executor(None, os.waitpid, _pty_pid, 0)
        _cleanup_login()
        raise HTTPException(
            status_code=500,
            detail="Login process timed out after receiving code",
        ) from None

    _log("info", f"Login process exited with code {exit_code}. Output: {_pty_output[-500:]}")
    _cleanup_login()

    if exit_code == 0:
        return AuthCallbackResponse(success=True, message="Authentication successful")

    return AuthCallbackResponse(
        success=False,
        message=f"Authentication failed (exit code {exit_code})",
    )


@router.get("/auth/logs", response_model=list[LogEntry])
async def auth_logs(since: str = Query(default="")) -> list[LogEntry]:
    """Return recent auth log entries for the frontend dev console."""
    entries = list(_log_buffer)
    if since:
        entries = [e for e in entries if e["ts"] > since]
    return [LogEntry(**e) for e in entries]
