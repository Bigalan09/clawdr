"""Application-layer ports (interfaces). No concrete implementations here."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from pathlib import Path

    from clawdr.domain.models import Project, ProjectId


class ProjectRepoPort(Protocol):
    """Port for persisting and retrieving projects."""

    async def list_all(self) -> list[Project]: ...

    async def add(self, project: Project) -> None: ...

    async def remove(self, project_id: ProjectId) -> None: ...


class TmuxPort(Protocol):
    """Port for tmux session/window management."""

    async def ensure_session(self, name: str) -> None: ...

    async def create_window(self, session: str, window: str, cwd: Path) -> None: ...

    async def send_keys(self, session: str, window: str, keys: str) -> None: ...

    async def kill_window(self, session: str, window: str) -> None: ...

    async def list_windows(self, session: str) -> list[str]: ...

    async def start_pipe(self, session: str, window: str, fifo: Path) -> None: ...
