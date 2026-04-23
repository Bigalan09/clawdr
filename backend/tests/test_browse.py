"""Tests for the /api/browse directory browsing endpoint."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

from fastapi.testclient import TestClient

if TYPE_CHECKING:
    from pathlib import Path

from clawdr.main import app

client = TestClient(app)


def test_browse_default_returns_home(tmp_path: Path) -> None:
    """When no path is given and no CLAWDR_BROWSE_ROOT, defaults to ~."""
    sub = tmp_path / "projects"
    sub.mkdir()
    with patch("clawdr.interface.api.browse._browse_root", return_value=tmp_path):
        resp = client.get("/api/browse")
    assert resp.status_code == 200
    data = resp.json()
    assert data["current"] == str(tmp_path)
    assert any(e["name"] == "projects" for e in data["entries"])


def test_browse_respects_browse_root_env(tmp_path: Path) -> None:
    """CLAWDR_BROWSE_ROOT should set the default browse directory."""
    sub = tmp_path / "mydir"
    sub.mkdir()
    with patch.dict("os.environ", {"CLAWDR_BROWSE_ROOT": str(tmp_path)}):
        resp = client.get("/api/browse")
    assert resp.status_code == 200
    data = resp.json()
    assert data["current"] == str(tmp_path)
    assert any(e["name"] == "mydir" for e in data["entries"])


def test_browse_subdirectory(tmp_path: Path) -> None:
    """Browsing a specific subdirectory works."""
    sub = tmp_path / "child"
    sub.mkdir()
    grandchild = sub / "grandchild"
    grandchild.mkdir()
    with patch("clawdr.interface.api.browse._browse_root", return_value=tmp_path):
        resp = client.get("/api/browse", params={"path": str(sub)})
    assert resp.status_code == 200
    data = resp.json()
    assert data["current"] == str(sub)
    assert data["parent"] == str(tmp_path)
    assert any(e["name"] == "grandchild" for e in data["entries"])


def test_browse_prevents_navigation_above_root(tmp_path: Path) -> None:
    """Requesting a path above the browse root should redirect to root."""
    root = tmp_path / "root"
    root.mkdir()
    with patch("clawdr.interface.api.browse._browse_root", return_value=root):
        resp = client.get("/api/browse", params={"path": str(tmp_path)})
    assert resp.status_code == 200
    data = resp.json()
    # Should be clamped back to root
    assert data["current"] == str(root)


def test_browse_root_has_no_parent(tmp_path: Path) -> None:
    """The browse root should not have a parent link."""
    with patch("clawdr.interface.api.browse._browse_root", return_value=tmp_path):
        resp = client.get("/api/browse", params={"path": str(tmp_path)})
    assert resp.status_code == 200
    data = resp.json()
    assert data["parent"] is None


def test_browse_hides_dotfiles(tmp_path: Path) -> None:
    """Hidden directories (starting with .) should be excluded."""
    (tmp_path / ".hidden").mkdir()
    (tmp_path / "visible").mkdir()
    with patch("clawdr.interface.api.browse._browse_root", return_value=tmp_path):
        resp = client.get("/api/browse", params={"path": str(tmp_path)})
    assert resp.status_code == 200
    names = [e["name"] for e in resp.json()["entries"]]
    assert "visible" in names
    assert ".hidden" not in names


def test_browse_excludes_files(tmp_path: Path) -> None:
    """Regular files should not appear in entries."""
    (tmp_path / "subdir").mkdir()
    (tmp_path / "file.txt").write_text("hello")
    with patch("clawdr.interface.api.browse._browse_root", return_value=tmp_path):
        resp = client.get("/api/browse", params={"path": str(tmp_path)})
    assert resp.status_code == 200
    names = [e["name"] for e in resp.json()["entries"]]
    assert "subdir" in names
    assert "file.txt" not in names


def test_browse_nonexistent_path_returns_404(tmp_path: Path) -> None:
    """A path that doesn't exist should return 404."""
    with patch("clawdr.interface.api.browse._browse_root", return_value=tmp_path):
        resp = client.get(
            "/api/browse",
            params={"path": str(tmp_path / "nope")},
        )
    assert resp.status_code == 404


def test_browse_file_path_returns_400(tmp_path: Path) -> None:
    """Browsing a file (not a dir) should return 400."""
    f = tmp_path / "afile.txt"
    f.write_text("hi")
    with patch("clawdr.interface.api.browse._browse_root", return_value=tmp_path):
        resp = client.get("/api/browse", params={"path": str(f)})
    assert resp.status_code == 400
