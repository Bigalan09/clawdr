"""Configuration schema and file resolution."""

from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel, Field

_APP_NAME = "clawdr"
_CONFIG_FILENAME = "config.yaml"


class TailscaleConfig(BaseModel):
    """Tailscale network binding configuration."""

    bind_host: str = "auto"
    port: int = Field(default=8787, ge=1, gt=0, le=65535)


class ProjectEntry(BaseModel):
    """A single project entry as it appears in the config file."""

    name: str
    path: str
    permission_mode: str = "default"


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: str = "info"
    format: str = "json"


class AppConfig(BaseModel):
    """Top-level application configuration loaded from config.yaml."""

    tailscale: TailscaleConfig = Field(default_factory=TailscaleConfig)
    projects: list[ProjectEntry] = Field(default_factory=list)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)


def resolve_config_path() -> Path:
    """Resolve the config file path.

    Resolution order:
    1. ``$CLAWDR_CONFIG`` environment variable
    2. ``$XDG_CONFIG_HOME/clawdr/config.yaml``
    3. ``~/.config/clawdr/config.yaml``
    """
    env_path = os.environ.get("CLAWDR_CONFIG")
    if env_path:
        return Path(env_path)

    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        return Path(xdg) / _APP_NAME / _CONFIG_FILENAME

    return Path.home() / ".config" / _APP_NAME / _CONFIG_FILENAME
