"""Tests for config schema, resolution, YAML loading, and project repo."""

from __future__ import annotations

from pathlib import Path

import pytest

from clawdr.domain.models import Project, ProjectId, ProjectNotFoundError
from clawdr.infrastructure.config import AppConfig, resolve_config_path
from clawdr.infrastructure.yaml_config import load_config, save_config
from clawdr.infrastructure.yaml_project_repo import YamlProjectRepo


class TestAppConfig:
    def test_defaults(self) -> None:
        config = AppConfig()
        assert config.tailscale.bind_host == "auto"
        assert config.tailscale.port == 8787
        assert config.projects == []
        assert config.logging.level == "info"
        assert config.logging.format == "json"

    def test_port_validation(self) -> None:
        with pytest.raises(Exception):  # noqa: B017
            AppConfig.model_validate({"tailscale": {"port": 0}})

    def test_port_upper_bound(self) -> None:
        with pytest.raises(Exception):  # noqa: B017
            AppConfig.model_validate({"tailscale": {"port": 70000}})


class TestResolveConfigPath:
    def test_clawdr_config_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CLAWDR_CONFIG", "/custom/config.yaml")
        monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
        assert resolve_config_path() == Path("/custom/config.yaml")

    def test_xdg_config_home(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("CLAWDR_CONFIG", raising=False)
        monkeypatch.setenv("XDG_CONFIG_HOME", "/xdg")
        assert resolve_config_path() == Path("/xdg/clawdr/config.yaml")

    def test_default_fallback(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("CLAWDR_CONFIG", raising=False)
        monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
        result = resolve_config_path()
        assert result == Path.home() / ".config" / "clawdr" / "config.yaml"


class TestYamlRoundTrip:
    def test_load_missing_file_returns_defaults(self, tmp_path: Path) -> None:
        config = load_config(tmp_path / "nonexistent.yaml")
        assert config.projects == []

    def test_save_and_load(self, tmp_path: Path) -> None:
        path = tmp_path / "config.yaml"
        original = AppConfig.model_validate(
            {
                "tailscale": {"bind_host": "100.1.2.3", "port": 9000},
                "projects": [
                    {"name": "Ledger Sync", "path": "/home/alan/ledger-sync"},
                ],
                "logging": {"level": "debug", "format": "console"},
            }
        )
        save_config(original, path)
        reloaded = load_config(path)
        assert reloaded.tailscale.bind_host == "100.1.2.3"
        assert reloaded.tailscale.port == 9000
        assert len(reloaded.projects) == 1
        assert reloaded.projects[0].name == "Ledger Sync"
        assert reloaded.logging.level == "debug"

    def test_load_empty_file(self, tmp_path: Path) -> None:
        path = tmp_path / "config.yaml"
        path.write_text("")
        config = load_config(path)
        assert config == AppConfig()


class TestYamlProjectRepo:
    @pytest.fixture()
    def repo(self, tmp_path: Path) -> YamlProjectRepo:
        config_path = tmp_path / "config.yaml"
        initial = AppConfig.model_validate(
            {
                "projects": [
                    {"name": "Ledger Sync", "path": "/home/alan/ledger-sync"},
                ],
            }
        )
        save_config(initial, config_path)
        return YamlProjectRepo(config_path)

    @pytest.mark.asyncio()
    async def test_list_all(self, repo: YamlProjectRepo) -> None:
        projects = await repo.list_all()
        assert len(projects) == 1
        assert projects[0].id == ProjectId("ledger-sync")
        assert projects[0].name == "Ledger Sync"

    @pytest.mark.asyncio()
    async def test_add_project(self, repo: YamlProjectRepo) -> None:
        new_proj = Project(
            id=ProjectId("gameboy-maze"),
            name="Gameboy Maze",
            path=Path("/home/alan/gameboy-maze"),
            source="ui",
        )
        await repo.add(new_proj)
        projects = await repo.list_all()
        assert len(projects) == 2
        names = {p.name for p in projects}
        assert names == {"Ledger Sync", "Gameboy Maze"}

    @pytest.mark.asyncio()
    async def test_add_duplicate_is_noop(self, repo: YamlProjectRepo) -> None:
        existing = Project(
            id=ProjectId("ledger-sync"),
            name="Ledger Sync",
            path=Path("/home/alan/ledger-sync"),
            source="config",
        )
        await repo.add(existing)
        projects = await repo.list_all()
        assert len(projects) == 1

    @pytest.mark.asyncio()
    async def test_remove_project(self, repo: YamlProjectRepo) -> None:
        await repo.remove(ProjectId("ledger-sync"))
        projects = await repo.list_all()
        assert len(projects) == 0

    @pytest.mark.asyncio()
    async def test_remove_nonexistent_raises(self, repo: YamlProjectRepo) -> None:
        with pytest.raises(ProjectNotFoundError):
            await repo.remove(ProjectId("nope"))

    @pytest.mark.asyncio()
    async def test_full_round_trip(self, tmp_path: Path) -> None:
        """CP-017: load, add, save, reload, verify all present."""
        config_path = tmp_path / "config.yaml"
        initial = AppConfig.model_validate(
            {
                "projects": [
                    {"name": "Alpha", "path": "/home/alan/alpha"},
                ],
            }
        )
        save_config(initial, config_path)

        repo = YamlProjectRepo(config_path)

        # Load initial
        projects = await repo.list_all()
        assert len(projects) == 1

        # Add a second project
        await repo.add(
            Project(
                id=ProjectId("beta"),
                name="Beta",
                path=Path("/home/alan/beta"),
                source="ui",
            )
        )

        # Reload from disk via a fresh repo instance
        repo2 = YamlProjectRepo(config_path)
        projects = await repo2.list_all()
        assert len(projects) == 2
        assert {p.id.value for p in projects} == {"alpha", "beta"}
