"""In-memory session store with asyncio lock."""

from __future__ import annotations

import asyncio

from clawdr.domain.models import ProjectId, Session, SessionState


class SessionStore:
    """Thread-safe in-memory store for active sessions."""

    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}
        self._lock = asyncio.Lock()

    async def get(self, project_id: ProjectId) -> Session:
        """Get or create a session for the given project."""
        async with self._lock:
            key = project_id.value
            if key not in self._sessions:
                self._sessions[key] = Session(project_id=project_id)
            return self._sessions[key]

    async def get_all(self) -> list[Session]:
        """Return all tracked sessions."""
        async with self._lock:
            return list(self._sessions.values())

    async def set(self, session: Session) -> None:
        """Store or update a session."""
        async with self._lock:
            self._sessions[session.project_id.value] = session

    async def remove(self, project_id: ProjectId) -> None:
        """Remove a session from the store."""
        async with self._lock:
            self._sessions.pop(project_id.value, None)

    async def get_state(self, project_id: ProjectId) -> SessionState:
        """Get the current state for a project, defaulting to STOPPED."""
        session = await self.get(project_id)
        return session.state
