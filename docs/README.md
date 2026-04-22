# ClawdR: Planning Pack

Web panel for managing Claude Code Remote Control sessions on a headless mini PC, accessed over Tailscale.

## Documents

1. **[CONSTITUTION.md](./CONSTITUTION.md)** engineering principles that every change is measured against
2. **[PRD.md](./PRD.md)** the problem, goals, users, success criteria
3. **[SPEC.md](./SPEC.md)** architecture, domain model, API contracts
4. **[PLAN.md](./PLAN.md)** staged implementation plan with exit criteria
5. **[TASKS.md](./TASKS.md)** ticket sized work items, ready for Todoist or Linear

## How to Use This Pack

- Read CONSTITUTION and PRD first, they frame everything
- SPEC is the reference for "how should this be built"
- PLAN sets the order
- TASKS is your todo list

When implementing, hand this entire directory to Claude Code as context. The `CLAUDE.md` at the repo root should be a short file pointing at these docs.

## Quick Start (once implementation begins)

```bash
# Backend
cd backend && uv sync
uv run uvicorn clawdr.main:app --reload

# Frontend
cd web && bun install && bun dev
```

## Tech Stack at a Glance

- **Backend**: Python 3.12, FastAPI, libtmux, structlog, ruamel.yaml, pydantic v2
- **Frontend**: Next.js 15 App Router, Bun, Tailwind 4, Zustand, qrcode.react
- **Infra**: systemd user service, Tailscale for access control, YAML config
