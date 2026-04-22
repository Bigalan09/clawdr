# ClawdR

Web panel for managing Claude Code Remote Control sessions on a headless mini PC, accessed over Tailscale.

See [`docs/README.md`](./docs/README.md) for the full planning pack.
See [`CLAUDE.md`](./CLAUDE.md) for agent working notes.

## Status

Pre implementation. Planning pack complete, Phase 0 not yet started.

## Quick Start

```bash
# Backend
cd backend && uv sync && uv run uvicorn clawdr.main:app --reload

# Frontend
cd web && bun install && bun dev
```

## License

Personal project, not licensed for redistribution.
