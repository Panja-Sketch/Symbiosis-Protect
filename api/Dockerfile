# Build context: repository root (the API reads data/seed and data/derived).
#   docker build -f api/Dockerfile -t symbiosis-api .
FROM python:3.12-slim AS base
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
RUN pip install --no-cache-dir uv==0.12.5
WORKDIR /app

COPY api/pyproject.toml api/uv.lock api/
RUN cd api && uv sync --frozen --no-dev

COPY api/app api/app
COPY data/seed data/seed
COPY data/derived data/derived

ENV PATH="/app/api/.venv/bin:$PATH" \
    STORAGE_BACKEND=gcs SCHEDULER_ENABLED=false
WORKDIR /app/api
RUN useradd --create-home --uid 10001 app && chown -R app /app
USER app
EXPOSE 8080
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1"]
