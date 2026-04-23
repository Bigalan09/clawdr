"""FastAPI application factory and ASGI entrypoint."""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from clawdr.application.event_bus import EventBus
from clawdr.application.session_store import SessionStore
from clawdr.infrastructure.config import resolve_config_path
from clawdr.infrastructure.yaml_project_repo import YamlProjectRepo
from clawdr.interface.api.auth import router as auth_router
from clawdr.interface.api.browse import router as browse_router
from clawdr.interface.api.health import router as health_router
from clawdr.interface.api.projects import init_projects_router
from clawdr.interface.api.projects import router as projects_router
from clawdr.interface.api.ws import init_ws_router
from clawdr.interface.api.ws import router as ws_router


def create_app() -> FastAPI:
    """Build the FastAPI app with all routers mounted."""
    app = FastAPI(title="ClawdR", version="0.1.0")

    cors_origins = os.environ.get(
        "CLAWDR_CORS_ORIGINS",
        "http://localhost:3000,http://localhost:3001",
    ).split(",")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    config_path = resolve_config_path()
    project_repo = YamlProjectRepo(config_path)
    session_store = SessionStore()
    event_bus = EventBus()

    init_projects_router(project_repo, session_store, event_bus)
    init_ws_router(event_bus)

    app.include_router(auth_router, prefix="/api")
    app.include_router(browse_router, prefix="/api")
    app.include_router(health_router, prefix="/api")
    app.include_router(projects_router, prefix="/api")
    app.include_router(ws_router)
    return app


app = create_app()
