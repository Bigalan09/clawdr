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
FROM python:3.12-slim

# Install Node.js 22 for Claude Code CLI and Next.js
RUN apt-get update && apt-get install -y --no-install-recommends \
    supervisor \
    curl \
    ca-certificates \
    gnupg \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key \
       | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_22.x nodistro main" \
       > /etc/apt/sources.list.d/nodesource.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends nodejs \
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

ENV BACKEND_PORT=8000
ENV FRONTEND_PORT=3000

WORKDIR /app
CMD ["supervisord", "-n", "-c", "/etc/supervisor/conf.d/clawdr.conf"]
