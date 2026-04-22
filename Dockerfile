# --- Backend build stage ---
FROM python:3.12-slim AS backend-build

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app/backend
COPY backend/ ./
RUN uv venv .venv && uv pip install --python .venv/bin/python .

# --- Frontend build stage ---
FROM oven/bun:1 AS frontend-build

WORKDIR /app/web
COPY web/package.json web/bun.lock* ./
RUN bun install --frozen-lockfile

COPY web/ ./

ARG NEXT_PUBLIC_API_URL=""
ARG NEXT_PUBLIC_WS_URL=""
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_WS_URL=$NEXT_PUBLIC_WS_URL

RUN bun run build

# --- Runtime image ---
FROM node:22-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    supervisor \
    python3 \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Install Claude Code CLI globally via npm
RUN npm install -g @anthropic-ai/claude-code

# Backend
WORKDIR /app/backend
COPY --from=backend-build /app/backend /app/backend

# Frontend
WORKDIR /app/web
COPY --from=frontend-build /app/web/.next ./.next
COPY --from=frontend-build /app/web/node_modules ./node_modules
COPY --from=frontend-build /app/web/package.json ./

# Supervisor config
COPY docker/supervisord.conf /etc/supervisor/conf.d/clawdr.conf

RUN mkdir -p /root/.config/clawdr /root/.claude

VOLUME ["/root/.claude"]
EXPOSE 8000 3000

WORKDIR /app
CMD ["supervisord", "-n", "-c", "/etc/supervisor/conf.d/clawdr.conf"]
