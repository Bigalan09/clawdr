"""Pure domain types. No third-party imports, no I/O."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from datetime import datetime
    from pathlib import Path

_SLUG_PATTERN = re.compile(r"^[a-z0-9][a-z0-9\-]*[a-z0-9]$|^[a-z0-9]$")


@dataclass(frozen=True)
class ProjectId:
    """URL-safe slug identifying a project, e.g. 'ledger-sync'."""

    value: str

    def __post_init__(self) -> None:
        if not _SLUG_PATTERN.match(self.value):
            msg = (
                f"ProjectId must be a lowercase slug (letters, digits, hyphens, "
                f"no leading/trailing hyphens): {self.value!r}"
            )
            raise ValueError(msg)


class PermissionMode(Enum):
    """Claude Code RC permission modes."""

    DEFAULT = "default"
    AUTO = "auto"
    BYPASS = "bypassPermissions"
    PLAN = "plan"
    DONT_ASK = "dontAsk"
    ACCEPT_EDITS = "acceptEdits"


@dataclass(frozen=True)
class Project:
    """A managed project directory."""

    id: ProjectId
    name: str
    path: Path
    source: Literal["config", "ui"]
    permission_mode: PermissionMode = PermissionMode.DEFAULT


class SessionState(Enum):
    """Lifecycle states for a Claude Code RC session."""

    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    CRASHED = "crashed"


@dataclass(frozen=True)
class SessionUrl:
    """Opaque wrapper for a session URL. ``__repr__`` never leaks the token."""

    value: str

    def __repr__(self) -> str:
        return "SessionUrl(<redacted>)"

    def __str__(self) -> str:
        return "SessionUrl(<redacted>)"


@dataclass
class Session:
    """Runtime state for one project's Claude Code RC session."""

    project_id: ProjectId
    state: SessionState = SessionState.STOPPED
    url: SessionUrl | None = None
    started_at: datetime | None = None
    last_output_at: datetime | None = None
    permission_mode: PermissionMode = PermissionMode.DEFAULT

    def start(
        self, now: datetime, permission_mode: PermissionMode | None = None
    ) -> None:
        """Transition to STARTING."""
        if self.state not in (SessionState.STOPPED, SessionState.CRASHED):
            msg = f"Cannot start session in state {self.state.value}"
            raise InvalidStateTransitionError(msg)
        self.state = SessionState.STARTING
        self.url = None
        self.started_at = now
        self.last_output_at = None
        if permission_mode is not None:
            self.permission_mode = permission_mode

    def mark_running(self, url: SessionUrl) -> None:
        """Transition to RUNNING once the URL has been captured."""
        if self.state != SessionState.STARTING:
            msg = f"Cannot mark running from state {self.state.value}"
            raise InvalidStateTransitionError(msg)
        self.state = SessionState.RUNNING
        self.url = url

    def stop(self) -> None:
        """Transition to STOPPED."""
        self.state = SessionState.STOPPED
        self.url = None
        self.started_at = None
        self.last_output_at = None

    def crash(self) -> None:
        """Transition to CRASHED."""
        self.state = SessionState.CRASHED
        self.url = None


# --- Domain exceptions ---


class DomainError(Exception):
    """Base for all domain-layer exceptions."""


class InvalidStateTransitionError(DomainError):
    """Raised when a session state transition is illegal."""


class ProjectNotFoundError(DomainError):
    """Raised when a project ID doesn't match any known project."""


class SessionAlreadyRunningError(DomainError):
    """Raised when trying to start a session that's already active."""
