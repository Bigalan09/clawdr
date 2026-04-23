"""Liveness and diagnostics endpoints."""

from fastapi import APIRouter, Query
from pydantic import BaseModel

from clawdr.infrastructure.log_buffer import entries as log_entries

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str


class LogEntry(BaseModel):
    ts: str
    level: str
    msg: str


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Return a static liveness payload."""
    return HealthResponse(status="ok")


@router.get("/logs", response_model=list[LogEntry])
async def logs(since: str = Query(default="")) -> list[LogEntry]:
    """Return recent log entries for the frontend dev console."""
    return [LogEntry(**e) for e in log_entries(since)]
