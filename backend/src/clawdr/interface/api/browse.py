"""Directory browsing endpoint for the folder picker."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(tags=["browse"])


def _browse_root() -> Path:
    """Return the configured browse root directory.

    Set ``CLAWDR_BROWSE_ROOT`` to constrain browsing to a mount point
    (e.g. ``/host-home`` inside Docker).  Defaults to the user home.
    """
    env = os.environ.get("CLAWDR_BROWSE_ROOT", "")
    if env:
        return Path(env).resolve()
    return Path.home()


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
    """Synchronous directory listing, constrained to the browse root."""
    root = _browse_root()
    target = Path(path).expanduser().resolve()

    # Prevent navigation above the browse root.
    if not (target == root or root in target.parents):
        target = root

    if not target.exists():
        msg = f"Path not found: {target}"
        raise FileNotFoundError(msg)
    if not target.is_dir():
        msg = f"Not a directory: {target}"
        raise NotADirectoryError(msg)

    # Only offer parent navigation when above the root.
    if target != root and target.parent != target:
        parent: str | None = str(target.parent)
    else:
        parent = None

    entries: list[DirEntry] = []
    for child in sorted(target.iterdir()):
        if child.name.startswith("."):
            continue
        if child.is_dir():
            entries.append(DirEntry(name=child.name, path=str(child), is_dir=True))

    return BrowseResponse(current=str(target), parent=parent, entries=entries)


@router.get("/browse", response_model=BrowseResponse)
async def browse_directory(path: str = "") -> BrowseResponse:
    """List directories at the given path.

    When *path* is empty the browse root is used (``CLAWDR_BROWSE_ROOT``
    env var, falling back to ``~``).
    """
    if not path:
        path = str(_browse_root())
    try:
        return _list_dirs(path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except NotADirectoryError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail="Permission denied") from exc
