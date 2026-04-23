"""Claude Code authentication status and OAuth flow endpoints."""

from __future__ import annotations

import asyncio
import json
import logging
import re

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(tags=["auth"])

logger = logging.getLogger(__name__)

_URL_PATTERN = re.compile(r"https://claude\.com/cai/oauth/authorize\S+")


class AuthStatusResponse(BaseModel):
    """Response for GET /api/auth/status."""

    logged_in: bool
    auth_method: str
    email: str | None = None


class AuthLoginResponse(BaseModel):
    """Response for POST /api/auth/login."""

    oauth_url: str


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


# Background login process kept alive until OAuth completes.
_login_proc: asyncio.subprocess.Process | None = None


@router.post("/auth/login", response_model=AuthLoginResponse)
async def auth_login() -> AuthLoginResponse:
    """Start the OAuth login flow and return the authorization URL.

    Spawns ``claude auth login``, reads its output line-by-line until
    the OAuth URL appears, then returns it.  The process stays alive in
    the background waiting for the user to complete the OAuth flow.
    """
    global _login_proc

    # Kill any lingering login process from a previous attempt.
    if _login_proc is not None and _login_proc.returncode is None:
        _login_proc.kill()
        await _login_proc.wait()
        _login_proc = None

    try:
        proc = await asyncio.create_subprocess_exec(
            "claude",
            "auth",
            "login",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail="claude CLI not found") from exc

    _login_proc = proc
    assert proc.stdout is not None

    # Read output line-by-line until we find the OAuth URL (max 15s).
    try:
        async with asyncio.timeout(15):
            async for raw_line in proc.stdout:
                line = raw_line.decode("utf-8", errors="replace")
                match = _URL_PATTERN.search(line)
                if match:
                    return AuthLoginResponse(oauth_url=match.group(0))
    except TimeoutError:
        proc.kill()
        await proc.wait()
        _login_proc = None
        raise HTTPException(
            status_code=500,
            detail="Timed out waiting for OAuth URL",
        ) from None

    # Process exited without printing a URL.
    _login_proc = None
    raise HTTPException(
        status_code=500,
        detail="claude auth login exited without providing an OAuth URL",
    )
