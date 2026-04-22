# ClawdR

Web panel for managing Claude Code Remote Control sessions on a headless mini PC, accessed over Tailscale.

## Features

- Start/stop Claude Code RC sessions per project from a web UI
- Real-time session state via WebSocket (no polling)
- QR code and copy-able URL for connecting to running sessions
- Configurable permission modes per project (default, auto, bypassPermissions, plan, dontAsk, acceptEdits)
- Server-side folder picker for adding projects
- Mobile-first responsive design with pagination
- Light/dark mode toggle
- Docker support with tmux included

## Quick Start (Local)

### Prerequisites

- Python 3.12+, [uv](https://github.com/astral-sh/uv)
- [Bun](https://bun.sh)
- [Claude Code CLI](https://claude.ai/code) installed and authenticated

### Backend

```bash
cd backend
uv sync
uv run uvicorn clawdr.main:app --host 127.0.0.1 --port 8000 --reload
```

### Frontend

```bash
cd web
bun install
bun dev
```

Open http://localhost:3000 in your browser.

## Quick Start (Docker)

### Two-service mode (recommended)

```bash
docker compose up --build
```

This starts the backend on port 8000 and frontend on port 3000.

### Single-container mode

```bash
docker compose --profile combined up clawdr --build
```

Both services run in one container using supervisord.

### Configuration

Projects are stored in `~/.config/clawdr/config.yaml` (mapped to a Docker volume). You can also add/remove projects from the web UI.

```yaml
tailscale:
  bind_host: "auto"
  port: 8787

projects:
  - name: "My Project"
    path: "/home/user/projects/my-project"
    permission_mode: "default"

logging:
  level: "info"
  format: "json"
```

## Development

### Backend commands

```bash
cd backend
uv run pytest                 # tests
uv run ruff check .           # lint
uv run ruff format .          # format
uv run mypy src               # typecheck (strict)
```

### Frontend commands

```bash
cd web
bun run build                 # production build
bun run lint                  # lint
bun run typecheck             # typecheck
```

## Architecture

```
browser/phone
  |
  | HTTP + WebSocket
  v
FastAPI backend (Python 3.12)
  |- REST API: /api/projects, /api/projects/{id}/session, /api/browse
  |- WebSocket: /ws (real-time state push)
  |- Session launcher: spawns `claude rc` as subprocess
  |- URL capture: tails stdout, parses session URL
  |- Config: YAML with ruamel.yaml (preserves comments)
  |
Next.js 15 frontend (Bun, Tailwind 4)
  |- Zustand store (reactive state)
  |- WebSocket client (auto-reconnect)
  |- QR code via qrcode.react
  |- Mobile-first, light/dark mode
```

## Docs

- [`docs/PRD.md`](./docs/PRD.md) - product requirements
- [`docs/SPEC.md`](./docs/SPEC.md) - technical specification
- [`docs/PLAN.md`](./docs/PLAN.md) - phased implementation plan
- [`docs/CONSTITUTION.md`](./docs/CONSTITUTION.md) - engineering principles

## License

Personal project, not licensed for redistribution.
