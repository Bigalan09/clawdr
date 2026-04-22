"""REST router for projects and sessions."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, HTTPException

from clawdr.domain.models import PermissionMode, Project
from clawdr.infrastructure.yaml_project_repo import _slugify
from clawdr.interface.api.schemas import (
    AddProjectRequest,
    ProjectListResponse,
    ProjectView,
    SessionActionResponse,
    SessionUrlResponse,
    StartSessionRequest,
)

if TYPE_CHECKING:
    from clawdr.application.event_bus import EventBus
    from clawdr.application.session_store import SessionStore
    from clawdr.infrastructure.yaml_project_repo import YamlProjectRepo

router = APIRouter(prefix="/projects", tags=["projects"])

# These get set by the app factory at startup.
_project_repo: YamlProjectRepo | None = None
_session_store: SessionStore | None = None
_event_bus: EventBus | None = None


def init_projects_router(
    project_repo: YamlProjectRepo,
    session_store: SessionStore,
    event_bus: EventBus,
) -> None:
    """Wire dependencies into the router. Called once at app startup."""
    global _project_repo, _session_store, _event_bus
    _project_repo = project_repo
    _session_store = session_store
    _event_bus = event_bus


def _repo() -> YamlProjectRepo:
    assert _project_repo is not None, "Router not initialized"
    return _project_repo


def _store() -> SessionStore:
    assert _session_store is not None, "Router not initialized"
    return _session_store


def _bus() -> EventBus:
    assert _event_bus is not None, "Router not initialized"
    return _event_bus


@router.get("", response_model=ProjectListResponse)
async def list_projects() -> ProjectListResponse:
    """List all projects with their current session state."""
    projects = await _repo().list_all()
    views: list[ProjectView] = []
    for p in projects:
        session = await _store().get(p.id)
        views.append(
            ProjectView(
                id=p.id.value,
                name=p.name,
                path=str(p.path),
                source=p.source,
                session_state=session.state.value,
                started_at=(
                    session.started_at.isoformat()
                    if session.started_at
                    else None
                ),
                permission_mode=p.permission_mode.value,
            )
        )
    return ProjectListResponse(projects=views)


@router.post("/{project_id}/session", response_model=SessionActionResponse)
async def start_session(
    project_id: str,
    body: StartSessionRequest | None = None,
) -> SessionActionResponse:
    """Start a Claude Code RC session for the given project."""
    from datetime import UTC, datetime

    from clawdr.application.event_bus import SessionStateChanged
    from clawdr.domain.models import (
        InvalidStateTransitionError,
        ProjectId,
    )
    from clawdr.infrastructure.session_launcher import launch_session

    projects = await _repo().list_all()
    project = next((p for p in projects if p.id.value == project_id), None)
    if project is None:
        raise HTTPException(status_code=404, detail=f"Project {project_id!r} not found")

    # Determine permission mode: request override > project default
    perm = project.permission_mode
    if body and body.permission_mode:
        try:
            perm = PermissionMode(body.permission_mode)
        except ValueError:
            raise HTTPException(  # noqa: B904
                status_code=400,
                detail=f"Invalid permission_mode: {body.permission_mode!r}",
            )

    session = await _store().get(ProjectId(project_id))
    try:
        session.start(datetime.now(UTC), permission_mode=perm)
    except InvalidStateTransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    await _store().set(session)

    await _bus().publish(
        SessionStateChanged(
            project_id=project_id,
            state=session.state.value,
            started_at=session.started_at.isoformat() if session.started_at else None,
        )
    )

    # Launch the actual claude rc process
    await launch_session(
        project_id=ProjectId(project_id),
        project_path=str(project.path),
        project_name=project.name,
        permission_mode=perm,
        session_store=_store(),
        event_bus=_bus(),
    )

    return SessionActionResponse(
        project_id=project_id,
        session_state=session.state.value,
    )


@router.delete("/{project_id}/session", response_model=SessionActionResponse)
async def stop_session(project_id: str) -> SessionActionResponse:
    """Stop the session for the given project."""
    from clawdr.application.event_bus import SessionStateChanged
    from clawdr.domain.models import ProjectId
    from clawdr.infrastructure.session_launcher import kill_session

    session = await _store().get(ProjectId(project_id))
    await kill_session(ProjectId(project_id))
    session.stop()
    await _store().set(session)

    await _bus().publish(
        SessionStateChanged(
            project_id=project_id,
            state=session.state.value,
        )
    )

    return SessionActionResponse(
        project_id=project_id,
        session_state=session.state.value,
    )


@router.get(
    "/{project_id}/session/url", response_model=SessionUrlResponse
)
async def get_session_url(project_id: str) -> SessionUrlResponse:
    """Get the session URL for a running project."""
    from clawdr.domain.models import ProjectId

    session = await _store().get(ProjectId(project_id))
    url = session.url.value if session.url else None
    return SessionUrlResponse(project_id=project_id, url=url)


@router.post("", response_model=ProjectView, status_code=201)
async def add_project(body: AddProjectRequest) -> ProjectView:
    """Add a new project."""
    from pathlib import Path

    from clawdr.application.event_bus import ProjectListChanged
    from clawdr.domain.models import ProjectId

    try:
        perm = PermissionMode(body.permission_mode)
    except ValueError:
        raise HTTPException(  # noqa: B904
            status_code=400,
            detail=f"Invalid permission_mode: {body.permission_mode!r}",
        )

    project = Project(
        id=ProjectId(_slugify(body.name)),
        name=body.name,
        path=Path(body.path),
        source="ui",
        permission_mode=perm,
    )
    await _repo().add(project)
    await _bus().publish(ProjectListChanged())

    return ProjectView(
        id=project.id.value,
        name=project.name,
        path=str(project.path),
        source=project.source,
        session_state="stopped",
        permission_mode=project.permission_mode.value,
    )


@router.delete("/{project_id}", status_code=204)
async def remove_project(project_id: str) -> None:
    """Remove a project."""
    from clawdr.application.event_bus import ProjectListChanged
    from clawdr.domain.models import ProjectId, ProjectNotFoundError
    from clawdr.infrastructure.session_launcher import kill_session

    try:
        await _repo().remove(ProjectId(project_id))
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    await kill_session(ProjectId(project_id))
    await _store().remove(ProjectId(project_id))
    await _bus().publish(ProjectListChanged())
