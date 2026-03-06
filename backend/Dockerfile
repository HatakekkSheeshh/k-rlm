# ─── Stage 1: build dependencies với Poetry ───────────────────────────────────
FROM python:3.11-slim AS builder

# Không tạo .pyc, không buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.8.3 \
    POETRY_HOME=/opt/poetry \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1

# Cài Poetry
RUN pip install --no-cache-dir "poetry==$POETRY_VERSION"

WORKDIR /app

# Copy dependency manifests trước (tận dụng Docker layer cache)
COPY pyproject.toml poetry.lock* ./

# Cài production deps (không dev)
RUN /opt/poetry/bin/poetry install --only main --no-root

# ─── Stage 2: runtime image (nhỏ hơn, không có Poetry) ───────────────────────
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Copy virtualenv từ builder
COPY --from=builder /app/.venv /app/.venv

# Copy source code
COPY app/ ./app/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
