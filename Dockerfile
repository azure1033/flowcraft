# syntax=docker/dockerfile:1

FROM python:3.12-slim

WORKDIR /app

# Install uv (fast Python package installer)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# ── Layer 1: Dependencies (cached unless pyproject.toml/uv.lock change) ──
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev

# ── Layer 2: Application code ──
COPY src/ ./src/
COPY schemas/ ./schemas/
COPY examples/ ./examples/

# Re-install (picks up local package changes, deps already cached)
RUN uv sync --frozen --no-dev

# Runtime config
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0
ENV PORT=8000

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --retries=3 --start-period=10s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')"

CMD ["uvicorn", "flowcraft.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
