"""Process-based session launcher for Claude Code RC.

Spawns `claude rc` as a subprocess, tails its output for the session URL,
and manages the process lifecycle. Works without tmux; the process runs
directly under the backend.
"""

from __future__ import annotations

import asyncio
import logging
import re
from typing import TYPE_CHECKING

from clawdr.application.event_bus import SessionStateChanged
from clawdr.domain.models import PermissionMode, SessionState, SessionUrl
from clawdr.infrastructure.log_buffer import log as buf_log

if TYPE_CHECKING:
    from clawdr.application.event_bus import EventBus
    from clawdr.application.session_store import SessionStore
    from clawdr.domain.models import ProjectId

logger = logging.getLogger(__name__)


class LaunchError(RuntimeError):
    """Raised when the claude rc subprocess fails to start."""


_URL_PATTERN = re.compile(r"https://claude\.ai/code/session_[a-zA-Z0-9_\-]+")
_ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")

# Map of project_id -> running subprocess
_processes: dict[str, asyncio.subprocess.Process] = {}
_watcher_tasks: set[asyncio.Task[None]] = set()


def _build_command(
    project_path: str,
    permission_mode: PermissionMode,
    project_name: str,
) -> list[str]:
    """Build the claude rc command."""
    cmd = ["claude", "rc", "--name", project_name]
    if permission_mode != PermissionMode.DEFAULT:
        cmd.extend(["--permission-mode", permission_mode.value])
    return cmd


def _ensure_workspace_trusted(project_path: str) -> None:
    """Mark a workspace as trusted in .claude.json so ``claude rc`` doesn't reject it."""
    import json
    from pathlib import Path

    config_path = Path.home() / ".claude.json"
    try:
        config = json.loads(config_path.read_text()) if config_path.exists() else {}
    except (json.JSONDecodeError, OSError):
        config = {}

    projects = config.setdefault("projects", {})
    entry = projects.setdefault(project_path, {})
    if not entry.get("hasTrustDialogAccepted"):
        entry["hasTrustDialogAccepted"] = True
        config_path.write_text(json.dumps(config, indent=2))
        logger.info("Marked %s as trusted in .claude.json", project_path)


async def launch_session(
    project_id: ProjectId,
    project_path: str,
    project_name: str,
    permission_mode: PermissionMode,
    session_store: SessionStore,
    event_bus: EventBus,
) -> None:
    """Spawn claude rc and start watching its output."""
    key = project_id.value

    # Kill any existing process for this project
    await kill_session(project_id)

    # Ensure the workspace is trusted before launching.
    _ensure_workspace_trusted(project_path)

    cmd = _build_command(project_path, permission_mode, project_name)
    buf_log("info", f"Launching session for {key}: {' '.join(cmd)} (cwd={project_path})")
    logger.info("Launching session for %s: %s", key, " ".join(cmd))

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=project_path,
        )
    except (FileNotFoundError, PermissionError, OSError) as exc:
        buf_log("error", f"Failed to launch session for {key}: {exc}")
        logger.error("Failed to launch session for %s: %s", key, exc)
        session = await session_store.get(project_id)
        if session.state == SessionState.STARTING:
            session.crash()
            await session_store.set(session)
            await event_bus.publish(SessionStateChanged(project_id=key, state=session.state.value))
        msg = str(exc)
        raise LaunchError(msg) from exc

    _processes[key] = proc

    # Start a watcher task that reads output and manages state
    task = asyncio.create_task(_watch_process(key, proc, session_store, event_bus))
    _watcher_tasks.add(task)
    task.add_done_callback(_watcher_tasks.discard)


async def kill_session(project_id: ProjectId) -> None:
    """Kill the process for a project if it's running."""
    key = project_id.value
    proc = _processes.pop(key, None)
    if proc is None:
        return
    if proc.returncode is None:
        proc.terminate()
        try:
            await asyncio.wait_for(proc.wait(), timeout=5)
        except TimeoutError:
            proc.kill()
            await proc.wait()
    logger.info("Killed session process for %s", key)


def is_running(project_id: ProjectId) -> bool:
    """Check if a process is alive for this project."""
    proc = _processes.get(project_id.value)
    return proc is not None and proc.returncode is None


async def _watch_process(
    project_id: str,
    proc: asyncio.subprocess.Process,
    session_store: SessionStore,
    event_bus: EventBus,
) -> None:
    """Read process output, capture URL, detect exit."""
    from clawdr.domain.models import ProjectId as PId

    pid = PId(project_id)
    url_found = False
    output_lines: list[str] = []
    assert proc.stdout is not None

    try:
        async for raw_line in proc.stdout:
            line = raw_line.decode("utf-8", errors="replace").rstrip()
            clean = _ANSI_ESCAPE.sub("", line)
            if clean.strip():
                output_lines.append(clean.strip())

            if not url_found:
                match = _URL_PATTERN.search(clean)
                if match:
                    url_found = True
                    url = match.group(0)
                    buf_log("info", f"Session {project_id}: captured RC URL")
                    session = await session_store.get(pid)
                    if session.state == SessionState.STARTING:
                        session.mark_running(SessionUrl(value=url))
                        await session_store.set(session)
                        await event_bus.publish(
                            SessionStateChanged(
                                project_id=project_id,
                                state=session.state.value,
                                url=url,
                            )
                        )
                        logger.info("Captured URL for %s", project_id)
    except asyncio.CancelledError:
        return

    # Process exited - check if it was expected
    await proc.wait()
    _processes.pop(project_id, None)

    session = await session_store.get(pid)
    if session.state in (SessionState.STARTING, SessionState.RUNNING):
        session.crash()
        await session_store.set(session)
        await event_bus.publish(
            SessionStateChanged(project_id=project_id, state=session.state.value)
        )
        last_output = " | ".join(output_lines[-5:]) if output_lines else "(no output)"
        buf_log(
            "error",
            f"Session {project_id} crashed (exit {proc.returncode}): {last_output}",
        )
        logger.warning(
            "Session process for %s exited with code %s",
            project_id,
            proc.returncode,
        )
