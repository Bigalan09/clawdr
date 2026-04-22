"""Directory browsing endpoint for the folder picker."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(tags=["browse"])


class DirEntry(BaseModel):
    """A single directory entry."""

    name: str
    path: str
    is_dir: bool


class BrowseResponse(BaseModel):
    """Response for GET /api/browse."""

    current: str
    parent: str | None
    entries: list[DirEntry]


def _list_dirs(path: str) -> BrowseResponse:
    """Synchronous directory listing."""
    target = Path(path).expanduser().resolve()

    if not target.exists():
        msg = f"Path not found: {target}"
        raise FileNotFoundError(msg)
    if not target.is_dir():
        msg = f"Not a directory: {target}"
        raise NotADirectoryError(msg)

    parent = str(target.parent) if target.parent != target else None

    entries: list[DirEntry] = []
    for child in sorted(target.iterdir()):
        if child.name.startswith("."):
            continue
        if child.is_dir():
            entries.append(
                DirEntry(name=child.name, path=str(child), is_dir=True)
            )

    return BrowseResponse(current=str(target), parent=parent, entries=entries)


@router.get("/browse", response_model=BrowseResponse)
async def browse_directory(path: str = "~") -> BrowseResponse:
    """List directories at the given path."""
    try:
        return _list_dirs(path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except NotADirectoryError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail="Permission denied") from exc
