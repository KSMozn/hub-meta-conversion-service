# syntax=docker/dockerfile:1.7
FROM python:3.13-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# --- builder ----------------------------------------------------------------
FROM base AS builder
RUN pip install --upgrade pip build

COPY pyproject.toml ./
RUN pip install --prefix=/install --no-deps . \
    && pip install --prefix=/install \
        "fastapi>=0.115" \
        "uvicorn[standard]>=0.32" \
        "pydantic>=2.9" \
        "pydantic-settings>=2.6" \
        "sqlalchemy>=2.0" \
        "psycopg[binary]>=3.2" \
        "alembic>=1.13" \
        "httpx>=0.27" \
        "tenacity>=9.0" \
        "python-json-logger>=2.0" \
        "google-cloud-secret-manager>=2.20"

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./

# --- runtime ---------------------------------------------------------------
FROM base AS runtime

COPY --from=builder /install /usr/local
COPY --from=builder /app /app

RUN useradd --create-home --uid 1001 hub && chown -R hub:hub /app
USER hub

ENV PORT=8080
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -fsS http://127.0.0.1:${PORT}/healthz || exit 1

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
