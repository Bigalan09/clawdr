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


class MkdirRequest(BaseModel):
    """Request body for POST /api/browse/mkdir."""

    parent: str
    name: str


def _validate_new_dir_name(name: str) -> str:
    """Return *name* if it is a safe single path segment, else raise ValueError."""
    cleaned = name.strip()
    if not cleaned:
        msg = "Folder name is required"
        raise ValueError(msg)
    if cleaned.startswith("."):
        msg = "Folder name cannot start with '.'"
        raise ValueError(msg)
    if "/" in cleaned or "\\" in cleaned or cleaned in {".", ".."}:
        msg = "Folder name cannot contain path separators"
        raise ValueError(msg)
    return cleaned


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


def _create_dir(parent_path: str, name: str) -> BrowseResponse:
    """Synchronous directory creation, constrained to the browse root.

    Returns the refreshed listing of *parent_path* on success.
    """
    clean_name = _validate_new_dir_name(name)
    root = _browse_root()
    parent = Path(parent_path).expanduser().resolve()
    if not (parent == root or root in parent.parents):
        msg = "Parent is outside browse root"
        raise ValueError(msg)
    if not parent.exists() or not parent.is_dir():
        msg = f"Parent not found: {parent}"
        raise FileNotFoundError(msg)

    target = parent / clean_name
    if target.exists():
        msg = f"Already exists: {clean_name}"
        raise FileExistsError(msg)

    target.mkdir(parents=False, exist_ok=False)
    return _list_dirs(str(parent))


@router.post("/browse/mkdir", response_model=BrowseResponse)
async def create_directory(req: MkdirRequest) -> BrowseResponse:
    """Create a new directory under *parent* and return the refreshed listing.

    *name* must be a single path segment (no separators, no leading dot).
    *parent* must resolve to a directory inside the browse root.
    """
    try:
        return _create_dir(req.parent, req.name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except FileExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail="Permission denied") from exc
    except OSError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
