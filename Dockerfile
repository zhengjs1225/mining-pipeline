# ── Stage 1: Build Frontend ──────────────────────────────
FROM node:22-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ── Stage 2: Python Runtime ──────────────────────────────
FROM python:3.12-slim
WORKDIR /app

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY pipeline/ ./pipeline/
COPY serve/ ./serve/
COPY eval/ ./eval/
COPY run.sh ./
COPY DATA_NOTES.md ./

# Copy built frontend from stage 1
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Create data directory
RUN mkdir -p /app/data

# Entrypoint: ingest data then start server
COPY docker-entrypoint.sh .
RUN chmod +x docker-entrypoint.sh

EXPOSE 8000
ENV FRONTEND_DIR=/app/frontend/dist
ENV SERVE_STATIC=true

ENTRYPOINT ["./docker-entrypoint.sh"]
