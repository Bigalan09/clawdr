# --- Backend build stage ---
FROM python:3.12-slim AS backend

RUN apt-get update && apt-get install -y --no-install-recommends \
    tmux \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install Claude Code CLI
RUN curl -fsSL https://claude.ai/install.sh | sh 2>/dev/null || true
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app/backend
COPY backend/pyproject.toml backend/uv.lock* ./
RUN uv sync --no-dev --no-install-project

COPY backend/ ./
RUN uv sync --no-dev

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

# --- Frontend runtime ---
FROM oven/bun:1-slim AS frontend

WORKDIR /app/web
COPY --from=frontend-build /app/web/.next/standalone ./
COPY --from=frontend-build /app/web/.next/static ./.next/static
COPY --from=frontend-build /app/web/public ./public

EXPOSE 3000
CMD ["bun", "server.js"]

# --- Final combined image (default) ---
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    tmux \
    curl \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install bun
RUN curl -fsSL https://bun.sh/install | bash
ENV PATH="/root/.bun/bin:$PATH"

# Install Claude Code CLI
RUN curl -fsSL https://claude.ai/install.sh | sh 2>/dev/null || true
ENV PATH="/root/.local/bin:$PATH"

# Backend
WORKDIR /app/backend
COPY --from=backend /app/backend /app/backend

# Frontend
WORKDIR /app/web
COPY --from=frontend-build /app/web/.next ./.next
COPY --from=frontend-build /app/web/node_modules ./node_modules
COPY --from=frontend-build /app/web/package.json ./
COPY --from=frontend-build /app/web/public ./public 2>/dev/null || true

# Supervisor config
COPY docker/supervisord.conf /etc/supervisor/conf.d/clawdr.conf

# Config directory
RUN mkdir -p /root/.config/clawdr

EXPOSE 8000 3000

WORKDIR /app
CMD ["supervisord", "-n", "-c", "/etc/supervisor/conf.d/clawdr.conf"]
