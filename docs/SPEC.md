# Technical Specification

**Project**: ClawdR
**Companion to**: PRD.md, CONSTITUTION.md
**Last updated**: 2026-04-21

## 1. System Overview

```
┌──────────────────────────┐
│  Browser / PWA           │
│  Next.js + Tailwind      │
└────────────┬─────────────┘
             │ HTTPS/WSS over Tailscale
             ▼
┌──────────────────────────┐
│  FastAPI backend         │
│  (systemd service)       │
│                          │
│  Interface layer         │
│   ├─ REST routers        │
│   └─ WS hub              │
│  Application layer       │
│   └─ Use cases           │
│  Domain layer            │
│   └─ Project, Session    │
│  Infrastructure layer    │
│   ├─ libtmux adapter     │
│   ├─ YAML config repo    │
│   └─ FIFO tailer         │
└────────────┬─────────────┘
             │ libtmux + FIFO tails
             ▼
┌──────────────────────────┐
│  tmux server             │
│  session: clawdr   │
│   ├─ window: project-a   │
│   ├─ window: project-b   │
│   └─ window: project-c   │
└──────────────────────────┘
```

## 2. Domain Model

```python
# Pure Python, no third party imports

@dataclass(frozen=True)
class ProjectId:
    value: str  # slug, e.g. "ledger-sync"

@dataclass(frozen=True)
class Project:
    id: ProjectId
    name: str
    path: Path
    source: Literal["config", "ui"]

class SessionState(Enum):
    STOPPED = "stopped"
    STARTING = "starting"   # tmux window created, claude rc not yet printed URL
    RUNNING = "running"     # URL captured
    CRASHED = "crashed"     # process exited unexpectedly

@dataclass
class Session:
    project_id: ProjectId
    state: SessionState
    url: SessionUrl | None
    started_at: datetime | None
    last_output_at: datetime | None

@dataclass(frozen=True)
class SessionUrl:
    """Opaque secret. __repr__ redacts the token portion."""
    value: str
    def __repr__(self) -> str: return "SessionUrl(<redacted>)"
```

## 3. Application Ports

```python
class TmuxPort(Protocol):
    async def ensure_session(self, name: str) -> None: ...
    async def create_window(self, session: str, window: str, cwd: Path) -> None: ...
    async def send_keys(self, session: str, window: str, keys: str) -> None: ...
    async def kill_window(self, session: str, window: str) -> None: ...
    async def list_windows(self, session: str) -> list[str]: ...
    async def start_pipe(self, session: str, window: str, fifo: Path) -> None: ...

class ProjectRepoPort(Protocol):
    async def list_all(self) -> list[Project]: ...
    async def add(self, project: Project) -> None: ...
    async def remove(self, id: ProjectId) -> None: ...

class SessionOutputPort(Protocol):
    async def tail(self, project: ProjectId) -> AsyncIterator[str]: ...

class EventBusPort(Protocol):
    async def publish(self, event: DomainEvent) -> None: ...
    def subscribe(self) -> AsyncIterator[DomainEvent]: ...
```

## 4. Use Cases

- `ListProjects()` -> `list[ProjectView]`
- `AddProject(name, path)` -> `Project`
- `RemoveProject(id)` -> `None`
- `StartSession(project_id)` -> `Session`
- `StopSession(project_id)` -> `None`
- `GetSessionUrl(project_id)` -> `SessionUrl | None`
- `StreamOutput(project_id)` -> `AsyncIterator[str]`
- `ReconcileState()` -> `None` (runs on startup and periodically)

## 5. Session Lifecycle

```
user taps "Start"
  -> POST /api/projects/{id}/session
  -> StartSession use case
    -> TmuxAdapter.ensure_session("clawdr")
    -> TmuxAdapter.create_window("clawdr", "<slug>", cwd=project.path)
    -> TmuxAdapter.start_pipe(..., fifo=/run/clawdr/<slug>.fifo)
    -> TmuxAdapter.send_keys(..., "claude rc\n")
    -> Session(state=STARTING)
    -> EventBus.publish(SessionStarting(project_id))
  -> FifoTailer starts tailing, feeds UrlParser
  -> UrlParser detects session URL pattern
    -> SessionStore.update(state=RUNNING, url=...)
    -> EventBus.publish(SessionRunning(project_id, url))
  -> WS hub pushes update to connected clients
```

## 6. URL Parsing

**Pattern**: `https://claude.ai/code/session_[a-zA-Z0-9_\-]+`

The parser:
- Receives lines from the FIFO tailer
- Strips ANSI escape codes
- Matches against the pattern
- Emits the first match once per window lifetime (second matches ignored)
- Unit tested against captured real output (stored in `tests/fixtures/`)

## 7. FIFO Tailer

For each started window, backend creates a named pipe at `/run/clawdr/<project_slug>.fifo`, then runs `tmux pipe-pane -o -t clawdr:<slug> 'cat >> <fifo>'`.

The tailer opens the FIFO for reading asynchronously and yields lines. On window kill, the pipe is closed via `tmux pipe-pane -t ... ` (empty command toggles off) and the FIFO is unlinked.

Fallback: if FIFO creation fails (permissions, filesystem), tailer falls back to polling `capture_pane` every 1s. Logged at warn level.

## 8. Config File

Location: `~/.config/clawdr/config.yaml`

```yaml
tailscale:
  bind_host: "100.x.y.z"   # or "auto" to detect
  port: 8787

projects:
  - name: "Ledger Sync"
    path: "/home/alan/projects/ledger-sync"
  - name: "Gameboy Maze"
    path: "/home/alan/projects/gameboy-maze"

logging:
  level: "info"
  format: "json"   # or "console" for dev
```

UI-added projects are persisted by writing back to this file. The config module uses ruamel.yaml to preserve comments and ordering.

## 9. HTTP API

All responses JSON, all errors follow RFC 7807 problem details.

| Method | Path | Purpose |
|--------|------|---------|
| GET | /api/health | liveness |
| GET | /api/projects | list projects with session state |
| POST | /api/projects | add a project `{name, path}` |
| DELETE | /api/projects/{id} | remove project |
| POST | /api/projects/{id}/session | start session |
| DELETE | /api/projects/{id}/session | stop session |
| GET | /api/projects/{id}/session/url | get URL (auth gated, short TTL cache) |

## 10. WebSocket API

Single endpoint: `/ws`

Server pushes events:
```json
{"type": "session.state", "project_id": "ledger-sync", "state": "running"}
{"type": "session.url",   "project_id": "ledger-sync", "url": "https://..."}
{"type": "session.output","project_id": "ledger-sync", "line": "..."}
{"type": "project.added", "project": {...}}
{"type": "project.removed", "project_id": "..."}
```

Client sends:
```json
{"type": "subscribe.output", "project_id": "ledger-sync"}
{"type": "unsubscribe.output", "project_id": "ledger-sync"}
```

Output streaming is opt in per project to avoid flooding clients with logs from sessions they're not watching.

## 11. Frontend

- Next.js 15 App Router
- Bun as package manager and dev runtime
- Tailwind 4
- `qrcode.react` for QR rendering client side
- Zustand for the project/session store
- Native WebSocket, reconnect with exponential backoff
- PWA manifest + service worker for homescreen install on iOS

Pages:
- `/` dashboard with project grid
- `/projects/[id]` detail view with terminal tail and QR

## 12. Deployment

Single mini PC, Debian 12 or Ubuntu 24.04 assumed.

- Backend runs as a user level systemd service (not root)
- Frontend built statically via `bun run build && next export` where possible, served by the FastAPI backend as static files, or standalone via `bun run start` on a different port behind Traefik
- FIFOs live under `/run/user/$UID/clawdr/` to avoid needing `/run` root perms

## 13. Logging and Observability

- `structlog` with JSON renderer in prod
- Request ID middleware for HTTP and WS
- Domain events logged at info
- Session URLs redacted via a custom processor
- Log destination: stdout (captured by systemd/journald)

## 14. Error Handling

- Domain exceptions are typed (`ProjectNotFound`, `SessionAlreadyRunning`, etc.)
- Application layer catches and maps to result types
- Interface layer maps result types to HTTP status codes
- Unhandled exceptions log at error with traceback and return 500 with a generic problem detail

## 15. Testing Strategy

- Unit: domain and application, no mocks, no I/O, fast
- Contract: each adapter has a set of tests that can run against either a real dependency or a fake, proving they behave identically
- Integration: a compose file with real tmux in a container, full lifecycle tests
- E2E: playwright against the built frontend, one happy path test

## 16. Open Questions

1. Do we want to capture and persist the history of past sessions? (out of scope v1, noted for v2)
2. Should output tailing be rate limited to avoid flooding? (probably yes, 100 lines/sec cap)
3. Behaviour when backend restarts while sessions are running? (reconcile from tmux list-windows, treat URLs as lost, user must reopen from the CLI or restart session)
