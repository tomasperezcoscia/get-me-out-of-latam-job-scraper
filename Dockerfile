# Stage 1: Build frontend
FROM node:20-slim AS frontend-builder
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# Stage 2: Python application
FROM python:3.12-slim
WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml README.md ./

# Install dependencies
RUN uv pip install --system -e "."

# Copy application code
COPY . .

# Copy built frontend
COPY --from=frontend-builder /frontend/dist ./frontend/dist

# Default command
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
