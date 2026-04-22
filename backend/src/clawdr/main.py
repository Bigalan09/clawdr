"""FastAPI application factory and ASGI entrypoint."""

from fastapi import FastAPI

from clawdr.interface.api.health import router as health_router


def create_app() -> FastAPI:
    """Build the FastAPI app with all routers mounted."""
    app = FastAPI(title="ClawdR", version="0.1.0")
    app.include_router(health_router, prefix="/api")
    return app


app = create_app()
