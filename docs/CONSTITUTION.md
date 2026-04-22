# Constitution

The non negotiable engineering principles for this project. Every PR, every artifact, every decision is measured against these.

## 1. Clean Architecture

Dependencies point inward. The domain knows nothing about FastAPI, tmux, or the filesystem.

- **Domain**: pure Python, no I/O. Project, Session, SessionState, etc.
- **Application**: use cases that orchestrate the domain. Takes ports (interfaces) as dependencies.
- **Infrastructure**: adapters. libtmux wrapper, YAML config repo, FIFO tailer.
- **Interface**: FastAPI routers, websocket hub, pydantic schemas.

The domain layer has zero third party imports beyond the standard library. If you're tempted to `import libtmux` in the domain, you're doing it wrong.

## 2. Separation of Concerns

Each module does one thing. The tmux wrapper does not parse URLs. The URL parser does not touch tmux. The websocket hub does not know what a project is.

## 3. Dependency Inversion

High level modules depend on abstractions. The session manager depends on a `TmuxPort` protocol, not on libtmux directly. This makes the whole thing testable without tmux installed.

## 4. Type Safety

Full type hints on every function signature. Run `mypy --strict` in CI. Pydantic v2 for boundary data (HTTP, WS, config).

## 5. Tests

- Domain and application: unit tested, no mocks needed because they're pure.
- Infrastructure adapters: integration tested where practical, contract tested where not.
- pytest with pytest-asyncio for async code.
- Target: meaningful coverage, not a percentage.

## 6. No God Objects

No class over ~200 lines. No function over ~40 lines. If it's bigger, it's doing too much.

## 7. Explicit Over Implicit

- No magic config loading from env vars scattered across files. One config module, loaded at startup, passed down.
- No global state. Dependencies injected via FastAPI's `Depends` or constructor injection.
- No silent failures. Errors are either handled or propagated, never swallowed.

## 8. Fail Fast, Fail Loud

Validate config at startup. If tmux isn't on PATH, exit with a clear message. Don't limp along and fail mysteriously three hours later.

## 9. Observability

Structured logging (JSON in prod, human readable in dev) via `structlog`. Every session lifecycle event (start, stop, URL captured, crash) gets logged with correlation IDs.

## 10. Commit Discipline

Conventional commits. Small, atomic commits. Each commit compiles and passes tests. No "WIP" or "fix" messages on main.

## 11. Python Specifics

- Python 3.12+
- `uv` for dependency management
- `ruff` for lint and format
- `mypy --strict` for types
- No `# type: ignore` without a comment explaining why
- `async` all the way down once you cross the boundary, no sync DB calls from async handlers

## 12. Frontend Specifics

- Next.js App Router, TypeScript strict mode
- Tailwind for styling, no CSS files unless absolutely required
- No client components unless there's genuine interactivity
- Server components for data fetching where possible
- Bun for install and dev, builds via `next build`
- No prop drilling past two levels, use context or a lightweight store (zustand if needed)

## 13. Security

- The backend binds to the Tailscale interface only, never 0.0.0.0.
- Session URLs are treated as secrets. Never logged, never persisted to disk.
- CORS locked to the Tailscale hostname of the frontend.
- No auth in v1 because Tailscale provides the perimeter, but design for auth middleware to slot in later.

## 14. No Premature Abstraction

Build the thing that solves today's problem. Don't add a plugin system for tmux alternatives before there's a second implementation. YAGNI.

## 15. Documentation

- Every public function has a docstring stating what, not how.
- README covers install, run, and troubleshoot.
- Architecture decisions live in `docs/adr/` as ADRs, numbered and dated.
- When behaviour changes, docs change in the same PR.
