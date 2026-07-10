#!/usr/bin/env bash
# Mining Intelligence Pipeline — Convenience Script
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

case "${1:-help}" in
    install)
        echo "==> Installing dependencies..."
        python3 -m pip install -r requirements.txt
        ;;

    ingest)
        echo "==> Running full data ingestion pipeline..."
        shift
        python3 -m pipeline.ingest "$@"
        ;;

    dry-run)
        echo "==> Dry run (no DB write)..."
        python3 -m pipeline.ingest --dry-run
        ;;

    serve)
        echo "==> Starting API server on http://0.0.0.0:8000 ..."
        python3 -m serve.app
        ;;

    eval)
        echo "==> Running evaluation..."
        shift
        python3 -m eval.evaluate --verbose "$@"
        ;;

    stats)
        echo "==> Vector store statistics..."
        python3 -c "
from pipeline.vector_store import VectorStore
store = VectorStore()
stats = store.get_stats()
print(f'Total documents: {stats[\"total\"]}')
print(f'By source: {stats[\"by_source\"]}')
print(f'By category: {stats[\"by_category\"]}')
"
        ;;

    query)
        question="${2:-近7天澳洲锂出口政策有何变化?}"
        echo "==> Querying: $question"
        curl -s -X POST http://localhost:8000/query \
            -H "Content-Type: application/json" \
            -d "{\"question\": \"$question\", \"top_k\": 5, \"generate_answer\": false}" \
            | python3 -m json.tool
        ;;

    help|*)
        echo "Usage: ./run.sh <command>"
        echo ""
        echo "Commands:"
        echo "  install       Install Python dependencies"
        echo "  ingest        Run full data ingestion pipeline"
        echo "  dry-run       Test scrapers without writing to DB"
        echo "  serve         Start FastAPI server on port 8000"
        echo "  eval          Run evaluation (recall@5)"
        echo "  stats         Show vector store statistics"
        echo "  query [q]     Query the API (default: Chinese lithium policy)"
        echo "  help          Show this help"
        ;;
esac
