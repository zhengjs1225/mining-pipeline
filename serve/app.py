"""
FastAPI service for querying the mining data pipeline.

Endpoints:
    GET  /health          — Health check + collection stats
    POST /query           — Natural language query with semantic search + LLM answer
    GET  /docs            — Auto-generated Swagger UI

Query example:
    POST /query
    {
        "question": "近7天澳洲锂出口政策有何变化?",
        "top_k": 5,
        "generate_answer": true
    }
"""

import json
import os
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from loguru import logger
from pydantic import BaseModel, Field

# Import pipeline modules
import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))

from pipeline.config import CHROMA_COLLECTION, LLM_BASE_URL, LLM_API_KEY, LLM_MODEL

# ── App Setup ────────────────────────────────────────────
app = FastAPI(
    title="矿枢 MinerPivot API",
    description="矿枢 MinerPivot — 三源聚合管线：新闻 / 政策 / 价格，数据枢纽，产业核心",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global state (auto-detect backend) ───────────────────
embedder = None
vector_store = None
backend_type = "lightweight"  # "chromadb" | "lightweight"


def _init_backend():
    """Initialize the best available backend. ChromaDB > lightweight TF-IDF."""
    global embedder, vector_store, backend_type

    if vector_store is not None:
        return

    # Try ChromaDB first
    try:
        from pipeline.embedder import Embedder
        from pipeline.vector_store import VectorStore
        embedder = Embedder()
        vector_store = VectorStore(collection_name=CHROMA_COLLECTION)
        backend_type = "chromadb"
        logger.info("Backend: ChromaDB + BGE-M3")
        return
    except (ImportError, Exception) as e:
        logger.warning(f"ChromaDB backend unavailable: {e}")

    # Fallback: lightweight TF-IDF
    from pipeline.lightweight_store import LightweightEmbedder, LightweightVectorStore
    vector_store = LightweightVectorStore()
    embedder = vector_store.embedder  # Use embedder loaded from tfidf.pkl
    if embedder is None:
        embedder = LightweightEmbedder()
    backend_type = "lightweight"
    logger.info("Backend: Lightweight TF-IDF + numpy")


def get_embedder():
    global embedder
    if embedder is None:
        _init_backend()
    return embedder


def get_vector_store():
    global vector_store
    if vector_store is None:
        _init_backend()
    return vector_store


# ── Models ───────────────────────────────────────────────

class QueryRequest(BaseModel):
    question: str = Field(
        ...,
        description="Natural language question about mining",
        examples=["近7天澳洲锂出口政策有何变化?"],
    )
    top_k: int = Field(5, ge=1, le=20, description="Number of documents to retrieve")
    generate_answer: bool = Field(
        True, description="Whether to generate an LLM answer from retrieved docs"
    )
    source_filter: Optional[str] = Field(
        None, description="Filter by source (e.g., disr_au, lme, rare_earth_cn)"
    )
    category_filter: Optional[str] = Field(
        None, description="Filter by category: news, policy, price"
    )
    days_filter: Optional[int] = Field(
        None, description="Only include documents from last N days"
    )


class RetrievedDocument(BaseModel):
    id: str
    title: str
    source: str
    category: str
    url: str
    published_at: str
    content_preview: str = Field(..., description="First 500 chars of content")
    relevance_score: float = Field(..., description="Cosine similarity (1 - distance)")


class QueryResponse(BaseModel):
    question: str
    answer: Optional[str] = None
    retrieved_docs: List[RetrievedDocument]
    total_in_store: int
    query_time_ms: float


class HealthResponse(BaseModel):
    status: str
    total_documents: int
    by_source: dict
    by_category: dict


# ── Routes ───────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check service health and collection statistics."""
    try:
        store = get_vector_store()
        stats = store.get_stats()
        return HealthResponse(
            status="healthy",
            total_documents=stats["total"],
            by_source=stats["by_source"],
            by_category=stats["by_category"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unhealthy: {str(e)}")


@app.post("/query", response_model=QueryResponse)
async def query(req: QueryRequest):
    """
    Natural language query over the mining intelligence corpus.

    Supports Chinese and English queries. Retrieves the top-k most relevant
    documents and optionally generates an LLM answer using the retrieved context.
    """
    import time
    start = time.time()

    try:
        emb = get_embedder()
        store = get_vector_store()
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to load models: {str(e)}"
        )

    # Generate query embedding
    query_embedding = emb.embed_query(req.question)

    # Search vector store (backend-aware branching)
    if backend_type == "lightweight":
        results = store.search(
            query_embedding=query_embedding,
            n_results=req.top_k,
            source_filter=req.source_filter,
            category_filter=req.category_filter,
            days_filter=req.days_filter,
        )
    else:
        # ChromaDB backend
        where_filter = {}
        if req.source_filter:
            where_filter["source"] = req.source_filter
        if req.category_filter:
            where_filter["category"] = req.category_filter
        results = store.search(
            query_embedding=query_embedding,
            n_results=req.top_k,
            where=where_filter if where_filter else None,
        )

    # Format retrieved documents
    retrieved_docs = []
    for r in results:
        meta = r["metadata"]
        # Compute relevance score from distance (cosine distance → similarity)
        distance = r.get("distance", 0.0)
        relevance = max(0.0, 1.0 - distance)

        retrieved_docs.append(
            RetrievedDocument(
                id=r["id"],
                title=meta.get("title", "Untitled"),
                source=meta.get("source", "unknown"),
                category=meta.get("category", "unknown"),
                url=meta.get("url", ""),
                published_at=meta.get("published_at", ""),
                content_preview=r["content"][:500] if r["content"] else "",
                relevance_score=round(relevance, 4),
            )
        )

    # Generate LLM answer if requested
    answer = None
    if req.generate_answer and retrieved_docs:
        answer = await _generate_answer(req.question, retrieved_docs)

    query_time = (time.time() - start) * 1000

    return QueryResponse(
        question=req.question,
        answer=answer,
        retrieved_docs=retrieved_docs,
        total_in_store=store.count(),
        query_time_ms=round(query_time, 1),
    )


async def _generate_answer(
    question: str, docs: List[RetrievedDocument]
) -> Optional[str]:
    """
    Generate an answer using an LLM with retrieved documents as context.

    Falls back gracefully if no LLM is configured.
    """
    if not LLM_API_KEY:
        logger.warning("No LLM_API_KEY configured — skipping answer generation")
        return (
            "⚠ LLM not configured. Set LLM_API_KEY and LLM_BASE_URL environment "
            "variables to enable answer generation. Below are the most relevant "
            "documents for your question."
        )

    try:
        import httpx

        # Build context from retrieved documents
        context_parts = []
        for i, doc in enumerate(docs):
            context_parts.append(
                f"[Document {i+1}] Source: {doc.source} | Date: {doc.published_at}\n"
                f"Title: {doc.title}\n"
                f"Content: {doc.content_preview}\n"
            )
        context = "\n".join(context_parts)

        # Build prompt
        system_prompt = (
            "You are a mining industry intelligence analyst. "
            "Answer the user's question based ONLY on the provided document context. "
            "If the context doesn't contain enough information, say so clearly. "
            "Cite which documents you used (by number). "
            "Answer in the same language as the question."
        )

        user_prompt = (
            f"Question: {question}\n\n"
            f"Relevant documents:\n{context}\n\n"
            f"Please answer the question based on the documents above."
        )

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{LLM_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {LLM_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": LLM_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.3,
                    "max_tokens": 1000,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    except Exception as e:
        logger.error(f"LLM answer generation failed: {e}")
        return f"⚠ Failed to generate answer: {str(e)}"


# ── Startup / Shutdown ───────────────────────────────────

@app.on_event("startup")
async def startup():
    global _scheduler
    logger.info("矿枢 MinerPivot API starting up...")
    # Pre-load embedder
    get_embedder()
    store = get_vector_store()
    stats = store.get_stats()
    logger.info(f"Vector store ready: {stats['total']} documents")
    # Start scheduler
    _scheduler = ScheduleRunner(_scheduled_query, _scheduled_push, interval=60)
    _scheduler.start()


@app.on_event("shutdown")
async def shutdown():
    global _scheduler
    if _scheduler:
        _scheduler.stop()
    logger.info("矿枢 MinerPivot API shutting down...")


# ── Schedule CRUD ──────────────────────────────────────────
from serve.scheduler import (
    list_schedules, get_schedule, create_schedule,
    update_schedule, delete_schedule, ScheduleRunner,
)


class ScheduleRequest(BaseModel):
    question: str = Field(..., description="Query to run on schedule")
    cron: str = Field("0 9 * * *", description="Cron expression (min hour dom mon dow)")
    top_k: int = Field(3, ge=1, le=10)
    source_filter: Optional[str] = None
    category_filter: Optional[str] = None
    enabled: bool = True


class ScheduleUpdateRequest(BaseModel):
    question: Optional[str] = None
    cron: Optional[str] = None
    top_k: Optional[int] = None
    source_filter: Optional[str] = None
    category_filter: Optional[str] = None
    enabled: Optional[bool] = None


@app.get("/schedules")
async def get_schedules():
    """List all scheduled tasks."""
    return list_schedules()


@app.post("/schedules")
async def create_schedule_endpoint(req: ScheduleRequest):
    """Create a new scheduled query."""
    return create_schedule(req.model_dump())


@app.put("/schedules/{schedule_id}")
async def update_schedule_endpoint(schedule_id: str, req: ScheduleUpdateRequest):
    """Update an existing schedule."""
    result = update_schedule(schedule_id, req.model_dump(exclude_none=True))
    if result is None:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return result


@app.delete("/schedules/{schedule_id}")
async def delete_schedule_endpoint(schedule_id: str):
    """Delete a schedule."""
    if not delete_schedule(schedule_id):
        raise HTTPException(status_code=404, detail="Schedule not found")
    return {"status": "deleted", "id": schedule_id}


# Shared query logic (used by both /query and scheduler)
async def _run_query(question: str, top_k: int, source_filter: str, category_filter: str) -> dict:
    """Run a query and return structured results."""
    import time
    start = time.time()
    emb = get_embedder()
    store = get_vector_store()
    query_embedding = emb.embed_query(question)
    if backend_type == "lightweight":
        results = store.search(query_embedding=query_embedding, n_results=top_k,
                               source_filter=source_filter, category_filter=category_filter)
    else:
        where_filter = {}
        if source_filter: where_filter["source"] = source_filter
        if category_filter: where_filter["category"] = category_filter
        results = store.search(query_embedding=query_embedding, n_results=top_k,
                               where=where_filter if where_filter else None)

    retrieved_docs = []
    for r in results:
        meta = r["metadata"]
        distance = r.get("distance", 0.0)
        retrieved_docs.append({
            "id": r["id"], "title": meta.get("title", "Untitled"),
            "source": meta.get("source", ""), "category": meta.get("category", ""),
            "url": meta.get("url", ""), "published_at": meta.get("published_at", ""),
            "content_preview": r["content"][:500] if r["content"] else "",
            "relevance_score": round(max(0.0, 1.0 - distance), 4),
        })

    # Generate answer
    answer = None
    if retrieved_docs:
        answer = await _generate_answer(question, [
            RetrievedDocument(**d) for d in retrieved_docs
        ])

    return {
        "question": question,
        "answer": answer,
        "retrieved_docs": retrieved_docs,
        "query_time_ms": round((time.time() - start) * 1000, 1),
    }


# ── Scheduler helpers ──────────────────────────────────────
async def _scheduled_query(question: str, top_k: int, source: str, category: str) -> dict:
    """Run a query by calling the local API endpoint (avoids circular imports)."""
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            "http://127.0.0.1:8000/query",
            json={"question": question, "top_k": top_k, "generate_answer": True,
                  "source_filter": source, "category_filter": category},
        )
        resp.raise_for_status()
        return resp.json()


async def _scheduled_push(message: str):
    """Push notification — logs to file."""
    logger.info(f"[SCHEDULE PUSH] {message[:200]}...")
    push_log = Path(__file__).resolve().parent.parent / "data" / "push_log.jsonl"
    push_log.parent.mkdir(parents=True, exist_ok=True)
    with open(push_log, "a") as f:
        f.write(json.dumps({"timestamp": __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc).isoformat(), "message": message}) + "\n")


_scheduler = None


# ── Serve frontend static files in production ─────────────
FRONTEND_DIR = os.getenv("FRONTEND_DIR", "")
SERVE_STATIC = os.getenv("SERVE_STATIC", "").lower() == "true"

if SERVE_STATIC and FRONTEND_DIR and Path(FRONTEND_DIR).exists():
    # Mount static assets (JS, CSS, images)
    assets_dir = Path(FRONTEND_DIR) / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    # Serve public files and SPA fallback
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """Serve frontend SPA — fallback to index.html."""
        file_path = Path(FRONTEND_DIR) / full_path
        if full_path and file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(Path(FRONTEND_DIR) / "index.html"))

    logger.info(f"Serving frontend static files from {FRONTEND_DIR}")


# ── Entry point ──────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
