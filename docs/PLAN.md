# Implementation Plan

A staged, vertical slice approach. Each phase ends with something runnable and demonstrable.

## Phase 0: Foundations (half a day)

Get the skeletons standing before any real logic.

- Repo structure per CONSTITUTION.md
- Backend: `uv init`, pyproject with fastapi, uvicorn, libtmux, structlog, ruamel.yaml, pydantic, pytest, mypy, ruff
- Frontend: `bun create next-app`, Tailwind, strict TS, zustand, qrcode.react
- CI: GitHub Actions running `ruff`, `mypy --strict`, `pytest`, `bun run lint`, `bun run build`
- Pre-commit hooks for format on commit
- Empty `/api/health` endpoint returning `{"status":"ok"}`
- Empty dashboard page that just says "ClawdR"

Exit criteria: `uv run uvicorn` serves health, `bun dev` serves the landing page, CI is green.

## Phase 1: Domain and Config (half a day)

Pure, no I/O, easy to test.

- Domain types (Project, ProjectId, Session, SessionState, SessionUrl)
- Config loader with schema validation
- ProjectRepo port + YAML adapter
- Full unit test coverage of domain and config

Exit criteria: a test loads a YAML fixture, gets back Project objects, and the config module survives a round trip (load, add, save, reload).

## Phase 2: tmux Integration (one day)

Get real sessions running from code.

- TmuxPort protocol
- libtmux adapter implementing it
- Contract tests that run against real tmux (skipped in CI without tmux)
- Integration test: create session, create window, send keys, list windows, kill window

Exit criteria: a pytest runs end to end creating a window that runs `echo hello`, captures its output, kills it.

## Phase 3: Session Start/Stop (one day)

First vertical slice.

- `StartSession` and `StopSession` use cases
- REST endpoints wired up
- In memory session state store
- Basic reconcile on startup (enumerate existing windows)
- Frontend: project grid with start/stop buttons, state badge
- Manual test: start a session from the UI on dev, see it running in tmux

Exit criteria: from the browser, I can start a `claude rc` session for a configured project, see it go to STARTING then RUNNING (after URL capture in phase 5), and stop it.

## Phase 4: WebSocket Hub (half a day)

Live updates, no more polling.

- WS endpoint
- Event bus in memory (asyncio queues)
- Frontend WS client with reconnect
- Zustand store subscribes to events and updates UI

Exit criteria: open the UI in two browser tabs, start a session in one, see state change live in the other.

## Phase 5: URL Capture (one day)

FIFO tailing and URL parsing.

- FIFO creation in `/run/user/$UID/clawdr/`
- `tmux pipe-pane` wiring
- Async tailer that yields lines
- URL parser with ANSI stripping
- Session state transitions to RUNNING on URL capture
- URL redaction in logs
- Unit tests against captured fixtures

Exit criteria: start a real `claude rc` session, backend detects the URL within a couple of seconds, pushes event to UI.

## Phase 6: QR and Detail View (half a day)

The phone workflow.

- `/projects/[id]` detail page
- QR code rendered client side from the URL
- Tap to copy URL
- Short TTL on URL fetch endpoint

Exit criteria: on my phone, I open the panel, tap a running project, see a QR, scan it into the Claude app.

## Phase 7: Live Output Stream (one day)

The monitoring feature.

- Per project output subscription over WS
- Frontend terminal component (keep it simple, no xterm.js unless necessary, just a styled pre element with auto scroll)
- Rate limiting at 100 lines/sec
- Max buffer size on client (last 1000 lines)

Exit criteria: start a session, the detail page shows live output, scrolling works, no flooding when `find /` runs.

## Phase 8: UI Project Management (half a day)

Round out the feature set.

- Add project form (name + path picker)
- Remove project confirm dialog
- Persisted to YAML via config adapter
- Path validation server side

Exit criteria: from the UI I can add a new project, see it in the list, start a session in it, remove it.

## Phase 9: systemd Packaging (half a day)

Make it boot.

- `clawdr.service` unit file (user level, `systemctl --user`)
- `install.sh` that sets up config dir, copies binary/venv, enables the service
- README installation section
- Lingering enabled so the user service runs without login

Exit criteria: reboot the mini PC, backend is up, frontend loads, existing tmux sessions are reconciled.

## Phase 10: Hardening (one day)

Polish and resilience.

- Graceful shutdown: stop tailers, close FIFOs, save state
- Reconnect logic on WS
- Error boundaries in the frontend
- Structured logs in prod
- Basic metrics endpoint (prometheus format) for later scraping
- Docs: README, ADRs for key decisions (why tmux, why FIFO over capture-pane, why Tailscale-only)

Exit criteria: kill the backend mid-session, restart it, everything reconnects cleanly. Logs are useful.

## Total Estimate

Around 7 days of focused work. Realistic calendar time depends on life, probably 2-3 weeks of evenings.

## Definition of Done

Each phase:
1. Code merged to main via PR
2. Tests passing in CI
3. `mypy --strict` clean
4. Manual smoke test on the mini PC
5. Docs updated if behaviour changed
