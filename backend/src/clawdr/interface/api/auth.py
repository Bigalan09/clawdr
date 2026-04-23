"""Claude Code authentication status endpoint."""

from __future__ import annotations

import asyncio
import json
import logging

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["auth"])

logger = logging.getLogger(__name__)


class AuthStatusResponse(BaseModel):
    """Response for GET /api/auth/status."""

    logged_in: bool
    auth_method: str
    email: str | None = None


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
