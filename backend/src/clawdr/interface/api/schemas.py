"""Pydantic request/response schemas for the REST API."""

from __future__ import annotations

from pydantic import BaseModel

PERMISSION_MODES = [
    "default",
    "auto",
    "bypassPermissions",
    "plan",
    "dontAsk",
    "acceptEdits",
]


class ProjectView(BaseModel):
    """A project with its current session state."""

    id: str
    name: str
    path: str
    source: str
    session_state: str
    started_at: str | None = None
    permission_mode: str = "default"


class ProjectListResponse(BaseModel):
    """Response for GET /api/projects."""

    projects: list[ProjectView]


class AddProjectRequest(BaseModel):
    """Request body for POST /api/projects."""

    name: str
    path: str
    permission_mode: str = "default"


class StartSessionRequest(BaseModel):
    """Request body for POST /api/projects/{id}/session."""

    permission_mode: str | None = None


class SessionActionResponse(BaseModel):
    """Response for session start/stop actions."""

    project_id: str
    session_state: str


class SessionUrlResponse(BaseModel):
    """Response for GET /api/projects/{id}/session/url."""

    project_id: str
    url: str | None = None
