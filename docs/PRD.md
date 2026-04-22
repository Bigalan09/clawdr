# Product Requirements Document

**Project**: ClawdR
**Owner**: Alan
**Status**: Draft v1
**Last updated**: 2026-04-21

## Problem

Claude Code Remote Control lets you drive a local session from a phone or browser, but the terminal side is bare. If you run multiple sessions across multiple projects on a headless mini PC, you have no easy way to:

1. See what's currently running
2. Start a session for a specific project without SSHing in
3. Get the session URL or QR code onto your phone quickly
4. Kill a session that's gone stale
5. Watch what a session is doing when you're away from the terminal

Manual tmux juggling over SSH works but is friction heavy, especially from a phone.

## Goal

A self hosted web panel running on a mini PC that provides a single UI for managing Claude Code Remote Control sessions across multiple projects. Access is limited to the user's Tailnet.

## Non Goals

- Not a replacement for the Claude app or claude.ai/code
- Not a cloud service, single user only
- Not a shell replacement, we're not reimplementing tmux in the browser
- No multi user, no RBAC, no SSO
- No scheduling, cron, or autonomous task running

## Users

One: Alan. Accessing from his laptop, desktop, and phone over Tailscale.

## Success Criteria

1. From my phone on cellular, I can open the panel, tap "start session for project X", and have a working Claude Code RC session I can connect to inside 10 seconds.
2. I can see at a glance which projects have live sessions and which are idle.
3. I can tail the output of a running session without SSHing.
4. The panel survives mini PC reboots and starts automatically.
5. If the backend crashes, restarting the systemd service recovers cleanly, picking up any tmux sessions that were already running.

## Core User Stories

**US1**: As a user, I want to see a list of my projects with live status, so I know what's running.

**US2**: As a user, I want to start a Remote Control session for a project with one tap, so I don't have to SSH in.

**US3**: As a user, I want to see the session URL and a QR code for a running session, so I can open it on my phone.

**US4**: As a user, I want to stop a session I'm done with, so resources are freed and the list stays clean.

**US5**: As a user, I want to watch live terminal output from a session, so I can monitor progress remotely.

**US6**: As a user, I want to add a new project via the UI, so I don't have to edit config files on the server.

**US7**: As a user, I want the panel to start on boot, so the mini PC is usable without manual intervention after power cycles.

## Constraints

- Mini PC runs Linux (Debian or Ubuntu assumed)
- tmux 3.3+ available
- Claude Code installed globally and authenticated on the mini PC
- Backend binds to Tailscale interface only
- Frontend served from the same host, behind Tailscale

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| `claude rc` output format changes, URL parser breaks | Parser is isolated, covered by tests with pinned sample output, fallback to manual URL entry |
| Session URL leaks via logs | Never log URLs, redact in structured logging middleware |
| tmux session state drifts from backend state | Backend treats tmux as source of truth, reconciles on every status poll |
| Claude Code auth expires on mini PC | Surface auth state in UI, link to docs for reauth |
| 10 min network timeout kills sessions during Tailscale hiccups | Out of scope to fix, document the limitation, add "restart" button |

## Out of Scope for v1

- Auth on the web UI (Tailscale is the perimeter)
- Multi host (one backend per mini PC)
- Mobile app (PWA is enough)
- Session history or replay
- Prompt queueing
- Notifications (use the Claude app's own push)
- Git worktree integration
