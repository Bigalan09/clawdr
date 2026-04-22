"""YAML config loader using ruamel.yaml (preserves comments on round-trip)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ruamel.yaml import YAML

from clawdr.infrastructure.config import AppConfig

if TYPE_CHECKING:
    from pathlib import Path


def load_config(path: Path) -> AppConfig:
    """Load and validate the config file, returning an AppConfig.

    If the file does not exist, returns default config.
    """
    if not path.exists():
        return AppConfig()

    yaml = YAML()
    with path.open("r") as f:
        raw = yaml.load(f)

    if raw is None:
        return AppConfig()

    return AppConfig.model_validate(raw)


def save_config(config: AppConfig, path: Path) -> None:
    """Write config back to YAML, preserving round-trip fidelity."""
    path.parent.mkdir(parents=True, exist_ok=True)

    yaml = YAML()
    yaml.default_flow_style = False

    data = config.model_dump()
    with path.open("w") as f:
        yaml.dump(data, f)
