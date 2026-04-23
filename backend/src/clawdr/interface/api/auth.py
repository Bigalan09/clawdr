"""Claude Code authentication status and OAuth flow endpoints."""

from __future__ import annotations

import asyncio
import json
import logging
import re
from urllib.parse import parse_qs, urlparse

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(tags=["auth"])

logger = logging.getLogger(__name__)

_OAUTH_URL_PATTERN = re.compile(r"https://claude\.com/cai/oauth/authorize\S+")
_ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]|\x1b\][^\x07]*\x07|\x1b[><=\[\]()][^\x1b]*")


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
        logger.error("Failed to check auth status: %s", exc)
        return AuthStatusResponse(logged_in=False, auth_method="error")

    try:
        data = json.loads(output.strip())
    except json.JSONDecodeError:
        logger.warning("Unexpected auth status output: %s", output[:200])
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


# State for the two-step login flow.
_login_proc: asyncio.subprocess.Process | None = None
_login_code_verifier: str | None = None


def _extract_code_verifier(oauth_url: str) -> str | None:
    """Extract code_challenge from the OAuth URL for PKCE tracking."""
    parsed = urlparse(oauth_url)
    params = parse_qs(parsed.query)
    challenges = params.get("code_challenge", [])
    return challenges[0] if challenges else None


@router.post("/auth/login", response_model=AuthLoginResponse)
async def auth_login() -> AuthLoginResponse:
    """Start the OAuth login flow and return the authorization URL.

    Uses ``script`` to wrap ``claude auth login`` in a PTY so that the
    CLI enters its interactive code-paste mode.  The process is kept
    alive so that ``POST /api/auth/callback`` can feed the code back.
    """
    global _login_proc, _login_code_verifier

    # Kill any lingering login process from a previous attempt.
    if _login_proc is not None and _login_proc.returncode is None:
        _login_proc.kill()
        await _login_proc.wait()
        _login_proc = None
        _login_code_verifier = None

    try:
        proc = await asyncio.create_subprocess_exec(
            "script",
            "-qc",
            "claude auth login",
            "/dev/null",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail="claude CLI not found") from exc

    _login_proc = proc
    assert proc.stdout is not None

    # Read output until we find the OAuth URL (max 30s, setup-token is slow).
    collected = ""
    try:
        async with asyncio.timeout(30):
            async for raw_line in proc.stdout:
                line = raw_line.decode("utf-8", errors="replace")
                collected += line
                clean = _ANSI_ESCAPE.sub("", collected)
                match = _OAUTH_URL_PATTERN.search(clean)
                if match:
                    url = match.group(0)
                    _login_code_verifier = _extract_code_verifier(url)
                    return AuthLoginResponse(oauth_url=url)
    except TimeoutError:
        proc.kill()
        await proc.wait()
        _login_proc = None
        raise HTTPException(
            status_code=500,
            detail="Timed out waiting for OAuth URL",
        ) from None

    _login_proc = None
    raise HTTPException(
        status_code=500,
        detail="claude auth login exited without providing an OAuth URL",
    )


@router.post("/auth/callback", response_model=AuthCallbackResponse)
async def auth_callback(body: AuthCallbackRequest) -> AuthCallbackResponse:
    """Feed the OAuth code back to the waiting ``claude auth login`` process."""
    global _login_proc, _login_code_verifier

    if _login_proc is None or _login_proc.returncode is not None:
        raise HTTPException(
            status_code=409,
            detail="No login process is waiting for a code. Call POST /api/auth/login first.",
        )

    assert _login_proc.stdin is not None

    # The process is in a PTY waiting at the "Paste code here" prompt.
    # Send the code followed by a newline.
    code_bytes = (body.code.strip() + "\n").encode()
    _login_proc.stdin.write(code_bytes)
    await _login_proc.stdin.drain()

    # Wait for the process to finish.
    try:
        await asyncio.wait_for(_login_proc.wait(), timeout=30)
    except TimeoutError:
        _login_proc.kill()
        await _login_proc.wait()
        _login_proc = None
        _login_code_verifier = None
        raise HTTPException(
            status_code=500,
            detail="Login process timed out after receiving code",
        ) from None

    exit_code = _login_proc.returncode
    _login_proc = None
    _login_code_verifier = None

    if exit_code == 0:
        return AuthCallbackResponse(success=True, message="Authentication successful")

    return AuthCallbackResponse(
        success=False,
        message=f"Authentication failed (exit code {exit_code})",
    )
