# syntax=docker/dockerfile:1

FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

COPY pyproject.toml uv.lock README.md ./
COPY src ./src
COPY static ./static
COPY restaurants ./restaurants

RUN uv sync --locked --no-dev --no-cache

FROM python:3.13-slim-bookworm AS runtime

WORKDIR /app

ENV BIND_HOST=0.0.0.0
ENV ENVIRONMENT=production
ENV FORWARDED_ALLOW_IPS=127.0.0.1
ENV PATH="/app/.venv/bin:${PATH}"
ENV PORT=8000
ENV PYTHONUNBUFFERED=1
ENV RESTAURANTS_ROOT=/app/restaurants
ENV STATIC_ROOT=/app/static

RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --home-dir /app \
      --shell /usr/sbin/nologin app

COPY --from=builder --chown=app:app /app /app

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.environ.get('PORT', '8000') + '/health/ready', timeout=2).read()"

CMD ["mallorca-pizza-serve"]
