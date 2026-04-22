# Tasks

Ticket sized, ready to drop into Todoist. Each has an ID matching `CP-XXX` for easy reference. Tags in brackets.

## Phase 0: Foundations

- [ ] **CP-001** Create monorepo structure with `backend/` and `web/` [infra]
- [ ] **CP-002** Backend: `uv init`, add base deps, configure ruff + mypy strict [infra]
- [ ] **CP-003** Frontend: `bun create next-app`, enable TS strict, install Tailwind + zustand + qrcode.react [infra]
- [ ] **CP-004** GitHub Actions: lint, typecheck, test for both backend and frontend [infra]
- [ ] **CP-005** Pre-commit hooks: ruff format, trailing whitespace, YAML lint [infra]
- [ ] **CP-006** `/api/health` endpoint returning `{"status":"ok"}` [backend]
- [ ] **CP-007** Landing page at `/` with "ClawdR" heading [frontend]
- [ ] **CP-008** README with setup instructions for local dev [docs]

## Phase 1: Domain and Config

- [ ] **CP-010** Domain types: ProjectId, Project, Session, SessionState, SessionUrl [domain]
- [ ] **CP-011** SessionUrl `__repr__` redacts token [domain][security]
- [ ] **CP-012** Unit tests for domain invariants [test]
- [ ] **CP-013** Config schema as pydantic model with validation [infra]
- [ ] **CP-014** YAML config loader using ruamel.yaml (preserves comments) [infra]
- [ ] **CP-015** ProjectRepoPort protocol [app]
- [ ] **CP-016** YamlProjectRepo adapter [infra]
- [ ] **CP-017** Round trip test: load, add, save, reload [test]
- [ ] **CP-018** Config file resolution: `$XDG_CONFIG_HOME/clawdr/config.yaml` with fallback [infra]

## Phase 2: tmux Integration

- [ ] **CP-020** TmuxPort protocol with full surface area [app]
- [ ] **CP-021** LibtmuxAdapter implementation [infra]
- [ ] **CP-022** Contract tests using real tmux, auto skipped when absent [test]
- [ ] **CP-023** Session name constant (`clawdr`) and slugifier helper [domain]
- [ ] **CP-024** Integration test: full window lifecycle with `echo hello` [test]
- [ ] **CP-025** Error mapping: libtmux exceptions -> domain exceptions [infra]

## Phase 3: Session Start/Stop

- [ ] **CP-030** In memory SessionStore with asyncio lock [app]
- [ ] **CP-031** StartSession use case [app]
- [ ] **CP-032** StopSession use case [app]
- [ ] **CP-033** Startup reconciliation: enumerate existing tmux windows [app]
- [ ] **CP-034** REST router: `POST/DELETE /api/projects/{id}/session` [interface]
- [ ] **CP-035** Pydantic request/response schemas [interface]
- [ ] **CP-036** Problem detail error handler [interface]
- [ ] **CP-037** Frontend: project grid component with start/stop buttons [frontend]
- [ ] **CP-038** Frontend: API client with typed responses [frontend]
- [ ] **CP-039** Frontend: state badge component (stopped, starting, running, crashed) [frontend]

## Phase 4: WebSocket Hub

- [ ] **CP-040** Domain events: SessionStarting, SessionRunning, SessionStopped, SessionCrashed [domain]
- [ ] **CP-041** In memory EventBus with asyncio queues [app]
- [ ] **CP-042** WS endpoint `/ws` with connection manager [interface]
- [ ] **CP-043** Event to WS message mapper [interface]
- [ ] **CP-044** Frontend WS client with exponential backoff reconnect [frontend]
- [ ] **CP-045** Zustand store with WS subscription [frontend]
- [ ] **CP-046** Two tab test scripted in playwright [test]

## Phase 5: URL Capture

- [ ] **CP-050** FIFO directory setup at `/run/user/$UID/clawdr/` [infra]
- [ ] **CP-051** Wire `tmux pipe-pane` when creating a window [infra]
- [ ] **CP-052** Async FIFO tailer yielding lines [infra]
- [ ] **CP-053** ANSI escape stripper utility [domain]
- [ ] **CP-054** UrlParser with `session_...` pattern [domain]
- [ ] **CP-055** Captured fixture: real `claude rc` output for parser tests [test]
- [ ] **CP-056** URL redaction processor for structlog [infra][security]
- [ ] **CP-057** Session transitions STARTING -> RUNNING on URL capture [app]
- [ ] **CP-058** Fallback to capture_pane polling if FIFO fails [infra]

## Phase 6: QR and Detail View

- [ ] **CP-060** Detail page route `/projects/[id]` [frontend]
- [ ] **CP-061** URL fetch endpoint with short TTL response header [backend]
- [ ] **CP-062** QR code component using qrcode.react [frontend]
- [ ] **CP-063** Copy URL button with clipboard API [frontend]
- [ ] **CP-064** PWA manifest and icons [frontend]
- [ ] **CP-065** Service worker for offline shell [frontend]

## Phase 7: Live Output Stream

- [ ] **CP-070** WS message types: `subscribe.output`, `session.output` [interface]
- [ ] **CP-071** Per client subscription tracking [interface]
- [ ] **CP-072** Rate limiter (token bucket, 100 lines/sec) [app]
- [ ] **CP-073** Terminal component (styled pre, auto scroll, pause on scroll up) [frontend]
- [ ] **CP-074** Client side ring buffer (1000 lines) [frontend]
- [ ] **CP-075** Backend test: high throughput session doesn't OOM [test]

## Phase 8: UI Project Management

- [ ] **CP-080** `POST /api/projects` with path validation [backend]
- [ ] **CP-081** `DELETE /api/projects/{id}` [backend]
- [ ] **CP-082** Config writeback preserves structure [backend]
- [ ] **CP-083** Add project modal with name + path field [frontend]
- [ ] **CP-084** Remove project confirm dialog [frontend]
- [ ] **CP-085** Path validation: exists, is dir, readable [backend]

## Phase 9: systemd Packaging

- [ ] **CP-090** `clawdr.service` user unit file [infra]
- [ ] **CP-091** `install.sh` script [infra]
- [ ] **CP-092** `loginctl enable-linger` documented for the user [docs]
- [ ] **CP-093** Bind host defaults to detected Tailscale IP [backend]
- [ ] **CP-094** README: install, enable, check status [docs]

## Phase 10: Hardening

- [ ] **CP-100** Graceful shutdown handler (SIGTERM) [backend]
- [ ] **CP-101** State persistence across backend restart (reconciliation v2) [backend]
- [ ] **CP-102** Error boundary component wrapping project detail [frontend]
- [ ] **CP-103** Structured logging middleware with request IDs [backend]
- [ ] **CP-104** `/metrics` endpoint in Prometheus format [backend]
- [ ] **CP-105** ADR-001: Why tmux over a custom pty manager [docs]
- [ ] **CP-106** ADR-002: Why FIFO over capture_pane polling [docs]
- [ ] **CP-107** ADR-003: Why Tailscale-only access and no auth in v1 [docs]
- [ ] **CP-108** ADR-004: Why FastAPI over Starlette [docs]

## Bug/Risk Tickets (to pick up as they surface)

- [ ] **CP-900** What happens when two users open the same project detail and both stop it? [concurrency]
- [ ] **CP-901** Handle tmux server death and auto restart [resilience]
- [ ] **CP-902** Observability: surface URL capture timeouts (no URL seen in 30s) [observability]
