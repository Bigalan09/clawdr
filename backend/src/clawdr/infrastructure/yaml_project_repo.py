"""ProjectRepoPort implementation backed by the YAML config file."""

from __future__ import annotations

import re
from pathlib import Path

from clawdr.domain.models import PermissionMode, Project, ProjectId, ProjectNotFoundError
from clawdr.infrastructure.config import ProjectEntry
from clawdr.infrastructure.yaml_config import load_config, save_config


def _slugify(name: str) -> str:
    """Convert a project name to a URL-safe slug."""
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug


class YamlProjectRepo:
    """Reads and writes projects from the YAML config file."""

    def __init__(self, config_path: Path) -> None:
        self._config_path = config_path

    async def list_all(self) -> list[Project]:
        """Load all projects from config."""
        config = load_config(self._config_path)
        return [self._entry_to_project(entry) for entry in config.projects]

    async def add(self, project: Project) -> None:
        """Add a project to the config and save."""
        config = load_config(self._config_path)

        for entry in config.projects:
            if _slugify(entry.name) == project.id.value:
                return  # already exists

        config.projects.append(
            ProjectEntry(
                name=project.name,
                path=str(project.path),
                permission_mode=project.permission_mode.value,
            )
        )
        save_config(config, self._config_path)

    async def remove(self, project_id: ProjectId) -> None:
        """Remove a project from the config and save."""
        config = load_config(self._config_path)
        original_len = len(config.projects)
        config.projects = [
            entry for entry in config.projects if _slugify(entry.name) != project_id.value
        ]
        if len(config.projects) == original_len:
            msg = f"Project {project_id.value!r} not found in config"
            raise ProjectNotFoundError(msg)
        save_config(config, self._config_path)

    @staticmethod
    def _entry_to_project(entry: ProjectEntry) -> Project:
        """Map a config entry to a domain Project."""
        slug = _slugify(entry.name)
        try:
            perm = PermissionMode(entry.permission_mode)
        except ValueError:
            perm = PermissionMode.DEFAULT
        return Project(
            id=ProjectId(slug),
            name=entry.name,
            path=Path(entry.path),
            source="config",
            permission_mode=perm,
        )
