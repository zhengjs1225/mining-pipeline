#!/usr/bin/env bash
set -e

echo "==> Mining Pipeline — Docker Entrypoint"
echo "==> Running data ingestion (seed data fallback)..."
cd /app
python -m pipeline.ingest --source mining_com 2>/dev/null || true

echo "==> Starting API server on port 8000..."
exec python -m serve.app
