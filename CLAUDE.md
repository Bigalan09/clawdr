# ClawdR

Web panel for managing Claude Code Remote Control sessions on a headless mini PC, accessed over Tailscale.

## Read These First

Before touching any code, read in order:

1. `docs/CONSTITUTION.md` the non negotiable engineering principles
2. `docs/PRD.md` what we're building and why
3. `docs/SPEC.md` the technical design
4. `docs/PLAN.md` the staged implementation plan
5. `docs/TASKS.md` ticket sized work items

Every change must be consistent with the constitution. If a task seems to require breaking a principle, stop and raise it, don't just do it.

## Repo Layout

```
.
├── backend/           Python 3.12, FastAPI, Clean Architecture
│   ├── pyproject.toml
│   └── src/clawdr/
│       ├── domain/          pure, no I/O
│       ├── application/     use cases + ports
│       ├── infrastructure/  adapters (libtmux, YAML, FIFO)
│       └── interface/       FastAPI routers, WS hub
├── web/               Next.js 15 App Router, Bun, Tailwind 4
├── docs/              planning and ADRs
└── .github/workflows/ CI
```

## Working Style

- Small commits, conventional format: `feat(backend): add ProjectRepo port`
- Each commit compiles and passes tests
- Tests alongside the code they exercise
- One feature per PR, even if it spans backend and frontend
- Never commit directly to main

## Commands

### Backend

```bash
cd backend
uv sync                       # install deps
uv run uvicorn clawdr.main:app --reload
uv run pytest                 # test
uv run ruff check .           # lint
uv run ruff format .          # format
uv run mypy src               # typecheck (must be --strict clean)
```

### Frontend

```bash
cd web
bun install
bun dev                       # dev server
bun run build                 # production build
bun run lint
bun run typecheck
```

## Definition of Done (per task)

1. Code matches the constitution
2. Types pass `mypy --strict` (backend) and `tsc --noEmit` (frontend)
3. Tests written and passing
4. Lint clean
5. Docs updated if behaviour changed
6. Manual smoke test performed

## Things to Never Do

- Import `libtmux` from the domain layer
- Log session URLs
- Add `# type: ignore` without an explaining comment
- Bind the backend to `0.0.0.0`
- Swallow exceptions silently
- Add an abstraction for a use case that doesn't yet exist

## Current Phase

Phase 0: Foundations. See `docs/PLAN.md` for exit criteria.
