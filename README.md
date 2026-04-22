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
- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) installed and authenticated

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

```bash
docker compose up --build
```

This starts the backend on port 8000 and the frontend on port 3000.

### Claude Code Authentication

The container needs Claude Code CLI authenticated to run `claude rc` sessions. There are three options:

#### Option 1: Mount host auth (recommended for personal use)

If you've already run `claude auth login` on your host machine, the compose file mounts `~/.claude` into the container by default. Your existing auth is shared automatically.

```bash
# Just works if you're already logged in on the host
docker compose up --build
```

#### Option 2: Interactive login inside the container

```bash
docker compose up -d
docker exec -it clawdr-clawdr-1 claude auth login
```

This opens an OAuth URL — paste it into your browser, complete the flow, and the token is stored in the container's `/root/.claude` volume (persisted across restarts).

#### Option 3: API key auth (Anthropic Console billing)

Set `ANTHROPIC_API_KEY` in your environment or `.env` file. This uses Console API billing instead of your Max/Pro subscription.

```bash
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env
docker compose up --build
```

### Project paths

The container mounts your home directory as `/host-home` (read-only) so `claude rc` can access your project files. When adding projects via the UI, use `/host-home/...` paths.

To mount specific directories instead, edit `docker-compose.yml`:

```yaml
volumes:
  - /path/to/projects:/projects
```

Then use `/projects/my-project` as the path in the UI.

### What's in the container

| Component | How it's installed | Purpose |
|-----------|-------------------|---------|
| Python 3.12 | Base image | FastAPI backend |
| Node.js 22 | Base image | Claude Code CLI runtime, Next.js |
| Claude Code CLI | `npm install -g @anthropic-ai/claude-code` | Runs `claude rc` sessions |
| supervisor | `apt-get install supervisor` | Runs backend + frontend |

## Configuration

Projects are stored in `~/.config/clawdr/config.yaml` (Docker volume). You can also add/remove projects from the web UI.

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

### Backend

```bash
cd backend
uv run pytest                 # tests
uv run ruff check .           # lint
uv run ruff format .          # format
uv run mypy src               # typecheck (strict)
```

### Frontend

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

- [`docs/PRD.md`](./docs/PRD.md) — product requirements
- [`docs/SPEC.md`](./docs/SPEC.md) — technical specification
- [`docs/PLAN.md`](./docs/PLAN.md) — phased implementation plan
- [`docs/CONSTITUTION.md`](./docs/CONSTITUTION.md) — engineering principles

## License

MIT License. See [LICENSE](./LICENSE) for details.
