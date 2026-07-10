#!/usr/bin/env python3
"""
Evaluation framework for mining intelligence pipeline.

Metrics:
1. recall@k — fraction of ground-truth questions where at least one relevant
   document appears in the top-k retrieved results.
2. Answer faithfulness — checks if LLM-generated answers are supported by
   the retrieved documents (using keyword overlap and factual consistency).

Usage:
    python -m eval.evaluate              # Run full evaluation
    python -m eval.evaluate --k 5        # Custom k value
    python -m eval.evaluate --verbose    # Print per-question details
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Tuple

# Add project root to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from loguru import logger
import pandas as pd

from pipeline.config import (
    CHROMA_COLLECTION,
    LLM_BASE_URL,
    LLM_API_KEY,
    LLM_MODEL,
)
from pipeline.embedder import Embedder
from pipeline.vector_store import VectorStore

from .ground_truth import GROUND_TRUTH


class MiningEval:
    """Evaluation harness for the mining pipeline."""

    def __init__(self, k: int = 5):
        self.k = k
        self.embedder = Embedder()
        self.vector_store = VectorStore(collection_name=CHROMA_COLLECTION)

        # Check if we have data
        count = self.vector_store.count()
        if count == 0:
            logger.warning(
                "Vector store is EMPTY! Run 'python -m pipeline.ingest' first "
                "to populate the database, or use demo data for evaluation."
            )
        else:
            logger.info(f"Vector store has {count} documents for evaluation")

    def evaluate(self, verbose: bool = False) -> Dict[str, Any]:
        """Run full evaluation: recall@k + answer faithfulness."""
        results = []

        for gt in GROUND_TRUTH:
            qid = gt["id"]
            question = gt["question"]
            expected_keywords = gt["keywords"]
            relevant_sources = gt["relevant_sources"]

            start = time.time()

            # ── Retrieve ──────────────────────────────
            q_emb = self.embedder.embed_query(question)

            retrieved = self.vector_store.search(
                query_embedding=q_emb,
                n_results=self.k,
            )

            elapsed_ms = (time.time() - start) * 1000

            # ── Compute recall@k ──────────────────────
            hit = self._compute_recall_hit(
                retrieved, relevant_sources, expected_keywords
            )

            results.append(
                {
                    "id": qid,
                    "question": question[:100],
                    "category": gt["category"],
                    "language": gt["language"],
                    "recall_hit": hit,
                    "num_retrieved": len(retrieved),
                    "retrieved_sources": [r["metadata"].get("source", "") for r in retrieved],
                    "query_time_ms": elapsed_ms,
                }
            )

            if verbose:
                status = "✓ HIT" if hit else "✗ MISS"
                logger.info(
                    f"[{qid}] {status} | {question[:80]}... | "
                    f"sources: {[r['metadata'].get('source','') for r in retrieved]} | "
                    f"{elapsed_ms:.0f}ms"
                )

        # ── Aggregate metrics ─────────────────────────
        df = pd.DataFrame(results)
        recall_at_k = df["recall_hit"].mean()

        by_category = {}
        for cat in df["category"].unique():
            cat_df = df[df["category"] == cat]
            by_category[cat] = {
                "recall@k": round(cat_df["recall_hit"].mean(), 4),
                "count": len(cat_df),
            }

        by_language = {}
        for lang in df["language"].unique():
            lang_df = df[df["language"] == lang]
            by_language[lang] = {
                "recall@k": round(lang_df["recall_hit"].mean(), 4),
                "count": len(lang_df),
            }

        avg_latency = df["query_time_ms"].mean()

        summary = {
            "k": self.k,
            "total_questions": len(GROUND_TRUTH),
            "recall_at_k": round(recall_at_k, 4),
            "by_category": by_category,
            "by_language": by_language,
            "avg_query_latency_ms": round(avg_latency, 1),
            "details": results if verbose else None,
        }

        return summary

    def _compute_recall_hit(
        self,
        retrieved: List[Dict],
        relevant_sources: List[str],
        expected_keywords: List[str],
    ) -> bool:
        """
        A "hit" means at least one retrieved document:
        1. Comes from a relevant source, AND
        2. Contains at least one expected keyword (case-insensitive)
        """
        for r in retrieved:
            meta = r["metadata"]
            source = meta.get("source", "")
            content = r.get("content", "").lower()
            title = meta.get("title", "").lower()

            combined = f"{content} {title}"

            # Source match?
            source_match = source in relevant_sources
            if not source_match:
                continue

            # Keyword match?
            keyword_match = any(
                kw.lower() in combined for kw in expected_keywords
            )
            if keyword_match:
                return True

        return False

    def evaluate_answer_faithfulness(
        self, verbose: bool = False
    ) -> Dict[str, Any]:
        """
        Evaluate LLM answer faithfulness.

        For each ground-truth question, we generate an LLM answer from
        retrieved context and check if the answer is factually supported
        by the retrieved documents.

        Uses keyword-overlap as a proxy for faithfulness when LLM is
        not available for judge-based evaluation.
        """
        if not LLM_API_KEY:
            logger.warning(
                "LLM not configured. Faithfulness eval will use keyword-overlap proxy."
            )

        results = []

        for gt in GROUND_TRUTH:
            qid = gt["id"]
            question = gt["question"]

            # Retrieve
            q_emb = self.embedder.embed_query(question)
            retrieved = self.vector_store.search(
                query_embedding=q_emb,
                n_results=self.k,
            )

            if not retrieved:
                results.append(
                    {
                        "id": qid,
                        "faithfulness": 0.0,
                        "error": "No documents retrieved",
                    }
                )
                continue

            # Build context from retrieved docs
            context = "\n\n".join(
                f"[{r['metadata'].get('source','')}] {r['content'][:1000]}"
                for r in retrieved
            )

            # Generate answer
            try:
                answer = self._generate_answer(question, context)

                # Compute faithfulness: what fraction of answer statements
                # are supported by the retrieved context?
                faith_score = self._compute_faithfulness(answer, context)

                results.append(
                    {
                        "id": qid,
                        "question": question[:100],
                        "answer": answer[:500],
                        "faithfulness": round(faith_score, 4),
                    }
                )

                if verbose:
                    logger.info(
                        f"[{qid}] Faithfulness={faith_score:.3f} | "
                        f"Answer: {answer[:100]}..."
                    )

            except Exception as e:
                logger.error(f"[{qid}] Faithfulness eval failed: {e}")
                results.append(
                    {
                        "id": qid,
                        "faithfulness": 0.0,
                        "error": str(e),
                    }
                )

        # Aggregate
        scores = [r["faithfulness"] for r in results if "faithfulness" in r]
        avg_faithfulness = sum(scores) / len(scores) if scores else 0.0

        return {
            "total": len(results),
            "avg_faithfulness": round(avg_faithfulness, 4),
            "details": results,
        }

    def _generate_answer(self, question: str, context: str) -> str:
        """Generate answer from context using LLM API."""
        import httpx

        system_prompt = (
            "Answer based ONLY on the provided context. "
            "If the context doesn't contain the answer, say so."
        )

        with httpx.Client(timeout=60.0) as client:
            resp = client.post(
                f"{LLM_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {LLM_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": LLM_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {
                            "role": "user",
                            "content": f"Question: {question}\n\nContext:\n{context}",
                        },
                    ],
                    "temperature": 0.0,
                    "max_tokens": 500,
                },
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]

    def _compute_faithfulness(self, answer: str, context: str) -> float:
        """
        Proxy faithfulness score based on keyword overlap.

        Real implementation would use an LLM judge (e.g., "Is the answer
        fully supported by the context? Rate 1-5") or NLI model.

        This proxy checks what fraction of key claims in the answer
        appear in the context.
        """
        # Split answer into sentences
        import re
        sentences = re.split(r"[。.！!？?\n]", answer)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]

        if not sentences:
            return 0.0

        # Check each sentence for support in context
        context_lower = context.lower()
        supported = 0

        for sent in sentences:
            sent_lower = sent.lower()
            # Extract key words (4+ chars to avoid noise)
            words = re.findall(r"[a-zA-Z一-鿿]{2,}", sent_lower)
            if not words:
                continue

            # What fraction of key words appear in context?
            matches = sum(1 for w in words if w in context_lower)
            ratio = matches / len(words) if words else 0
            if ratio >= 0.5:  # At least half the key words in context
                supported += 1

        return supported / len(sentences) if sentences else 0.0


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate mining intelligence pipeline"
    )
    parser.add_argument(
        "--k", type=int, default=5, help="k for recall@k (default: 5)"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Print per-question details"
    )
    parser.add_argument(
        "--faithfulness", action="store_true",
        help="Also evaluate answer faithfulness"
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Save results to JSON file"
    )
    args = parser.parse_args()

    evaluator = MiningEval(k=args.k)

    # ── Recall@k ──────────────────────────────────────
    logger.info(f"\n{'='*60}")
    logger.info(f"EVALUATION: Recall@{args.k}")
    logger.info(f"{'='*60}")

    recall_results = evaluator.evaluate(verbose=args.verbose)

    print("\n" + "=" * 60)
    print(f"RECALL@{args.k} RESULTS")
    print("=" * 60)
    print(f"Overall Recall@{args.k}: {recall_results['recall_at_k']:.2%}")
    print(f"Total questions: {recall_results['total_questions']}")
    print(f"Avg latency: {recall_results['avg_query_latency_ms']:.1f}ms")
    print(f"\nBy category:")
    for cat, stats in recall_results["by_category"].items():
        print(f"  {cat}: Recall@{args.k} = {stats['recall@k']:.2%} ({stats['count']} Q)")
    print(f"\nBy language:")
    for lang, stats in recall_results["by_language"].items():
        print(f"  {lang}: Recall@{args.k} = {stats['recall@k']:.2%} ({stats['count']} Q)")

    # ── Faithfulness ──────────────────────────────────
    if args.faithfulness:
        logger.info(f"\n{'='*60}")
        logger.info("EVALUATION: Answer Faithfulness")
        logger.info(f"{'='*60}")

        faith_results = evaluator.evaluate_answer_faithfulness(
            verbose=args.verbose
        )

        print(f"\nAnswer Faithfulness: {faith_results['avg_faithfulness']:.2%}")

        # Merge results for output
        full_results = {
            "recall": recall_results,
            "faithfulness": faith_results,
        }
    else:
        full_results = {"recall": recall_results}

    # ── Save ──────────────────────────────────────────
    if args.output:
        output_path = Path(args.output)
        # Convert to serializable format
        output_data = {
            "recall": {
                "k": recall_results["k"],
                "total_questions": recall_results["total_questions"],
                "recall_at_k": recall_results["recall_at_k"],
                "by_category": recall_results["by_category"],
                "by_language": recall_results["by_language"],
                "avg_query_latency_ms": recall_results["avg_query_latency_ms"],
                "details": recall_results.get("details"),
            }
        }
        output_path.write_text(
            json.dumps(output_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        logger.info(f"Results saved to {output_path}")


if __name__ == "__main__":
    main()
