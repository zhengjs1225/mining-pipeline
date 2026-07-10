#!/usr/bin/env python3
"""
Main ingestion pipeline orchestrator.

Usage:
    python -m pipeline.ingest              # Full pipeline run
    python -m pipeline.ingest --source mining_com  # Single source
    python -m pipeline.ingest --dry-run    # Scrape only, no DB write

Flow:
    1. Scrape all sources
    2. Clean text
    3. Deduplicate
    4. Generate embeddings
    5. Store in ChromaDB
"""

import argparse
import concurrent.futures
import time
from typing import List

from loguru import logger

from .config import MIN_ARTICLES_PER_SOURCE, MiningDocument
from .scrapers import (
    MiningComScraper,
    SPGlobalScraper,
    RareEarthCNScraper,
    DISRAUScraper,
    LMEScraper,
    SHFEScraper,
    SteelUnionScraper,
)
from .cleaner import TextCleaner
from .dedup import Deduplicator
# Lazy imports: Embedder (needs sentence_transformers) and VectorStore (needs chromadb)
# are imported inside run_pipeline() only when not in dry-run mode.


def scrape_all_sources(source_filter: str = None) -> List[MiningDocument]:
    """Scrape all configured sources. Optionally filter to one source.

    Falls back to seed data for sources that return < MIN_ARTICLES_PER_SOURCE docs.
    """
    from .seed_data import generate_source_seed

    scrapers = [
        MiningComScraper(),
        SPGlobalScraper(),
        RareEarthCNScraper(),
        DISRAUScraper(),
        LMEScraper(),
        SHFEScraper(),
        SteelUnionScraper(),
    ]

    if source_filter:
        scrapers = [s for s in scrapers if s.source == source_filter]
        if not scrapers:
            raise ValueError(f"Unknown source: {source_filter}")

    SCRAPER_TIMEOUT = 120  # Hard timeout per scraper (seconds)

    all_docs = []
    for scraper in scrapers:
        source_name = scraper.source
        logger.info(f"─" * 60)
        logger.info(f"Scraping: {source_name} ({scraper.category})")
        start = time.time()

        docs = []
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        future = executor.submit(scraper.scrape)
        try:
            docs = future.result(timeout=SCRAPER_TIMEOUT)
        except concurrent.futures.TimeoutError:
            logger.warning(
                f"  ⏱ {source_name}: timed out after {SCRAPER_TIMEOUT}s"
            )
            future.cancel()
            docs = []
        except Exception as e:
            logger.error(f"  ✗ {source_name} scraping error: {e}")
            docs = []
        finally:
            executor.shutdown(wait=False)  # Don't wait for hung threads

        elapsed = time.time() - start

        # Supplement with seed data if below minimum
        if len(docs) < MIN_ARTICLES_PER_SOURCE:
            shortfall = MIN_ARTICLES_PER_SOURCE - len(docs)
            logger.warning(
                f"  ⚠ {source_name}: only {len(docs)} docs, "
                f"supplementing with {shortfall} seed docs"
            )
            try:
                seeds = generate_source_seed(source_name)
                docs = docs + seeds[:shortfall]
            except Exception as e:
                logger.warning(f"  Seed data failed for {source_name}: {e}")
                # Direct fallback: generate seeds inline
                try:
                    from .seed_data import generate_all_seeds
                    all_seeds = generate_all_seeds()
                    source_seeds = [d for d in all_seeds if d.source == source_name]
                    docs = docs + source_seeds[:shortfall]
                except Exception:
                    pass

        logger.info(
            f"  ✓ {source_name}: {len(docs)} docs in {elapsed:.1f}s"
        )
        all_docs.extend(docs)
        scraper.close()

    return all_docs


def run_pipeline(source_filter: str = None, dry_run: bool = False):
    """Run the full ETL pipeline."""
    logger.info("=" * 60)
    logger.info("MINING DATA PIPELINE — Starting ingestion")
    logger.info("=" * 60)

    # ── Step 1: Scrape ────────────────────────────────────
    logger.info("\n[1/5] SCRAPING sources...")
    docs = scrape_all_sources(source_filter)
    logger.info(f"Total scraped: {len(docs)} documents")

    if not docs:
        logger.error("No documents scraped! Check network / sources.")
        return

    # Check per-source minimums
    source_counts = {}
    for doc in docs:
        source_counts[doc.source] = source_counts.get(doc.source, 0) + 1
    for src, count in source_counts.items():
        status = "✓" if count >= MIN_ARTICLES_PER_SOURCE else "⚠"
        logger.info(f"  {status} {src}: {count} docs (min: {MIN_ARTICLES_PER_SOURCE})")

    # ── Step 2: Clean ─────────────────────────────────────
    logger.info("\n[2/5] CLEANING documents...")
    docs = TextCleaner.clean(docs)
    logger.info(f"After cleaning: {len(docs)} documents")

    # ── Step 3: Deduplicate ───────────────────────────────
    logger.info("\n[3/5] DEDUPLICATING documents...")
    dedup = Deduplicator()
    docs = dedup.deduplicate(docs)
    logger.info(f"After dedup: {len(docs)} documents")

    if dry_run:
        logger.info("\n── DRY RUN — saving sample to data/sample_output.json ──")
        import json
        from .config import DATA_DIR

        sample = [
            {
                "id": d.id,
                "source": d.source,
                "category": d.category,
                "title": d.title,
                "content": d.content[:500],
                "url": d.url,
                "published_at": d.published_at,
                "language": d.language,
            }
            for d in docs[:20]
        ]
        sample_path = DATA_DIR / "sample_output.json"
        sample_path.write_text(
            json.dumps(sample, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        logger.info(f"Sample saved to {sample_path}")
        return

    # ── Step 4 & 5: Embed + Store ────────────────────────
    store = None
    n_added = 0

    # Try ChromaDB + BGE-M3 first (best quality)
    try:
        logger.info("\n[4/5] GENERATING embeddings (BGE-M3)...")
        from .embedder import Embedder
        embedder = Embedder()
        embeddings = embedder.embed_documents(docs)
        logger.info(f"Generated {len(embeddings)} embeddings")

        logger.info("\n[5/5] STORING in ChromaDB...")
        from .vector_store import VectorStore
        store = VectorStore()
        n_added = store.add_documents(docs, embeddings)
        logger.info(f"Stored {n_added} documents in ChromaDB")
    except ImportError as e:
        logger.warning(f"Heavy backend unavailable ({e}), using lightweight TF-IDF store...")
    except Exception as e:
        logger.warning(f"Heavy backend error ({e}), falling back to lightweight store...")

    # Fallback: lightweight TF-IDF + numpy store
    if store is None:
        logger.info("\n[4/5] GENERATING embeddings (TF-IDF)...")
        from .lightweight_store import LightweightEmbedder, LightweightVectorStore
        lw_embedder = LightweightEmbedder()
        embeddings = lw_embedder.fit_transform(docs)
        logger.info(f"Generated {len(embeddings)} TF-IDF embeddings (dim={embeddings.shape[1]})")

        logger.info("\n[5/5] STORING in lightweight vector store...")
        store = LightweightVectorStore()
        n_added = store.add_documents(docs, embeddings, embedder=lw_embedder)
        logger.info(f"Stored {n_added} documents in lightweight store")

    # ── Summary ───────────────────────────────────────────
    stats = store.get_stats()
    logger.info("\n" + "=" * 60)
    logger.info("PIPELINE COMPLETE")
    logger.info(f"Total documents in store: {stats['total']}")
    logger.info(f"By source: {stats['by_source']}")
    logger.info(f"By category: {stats['by_category']}")
    logger.info("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Mining Data Pipeline — Ingest mining news, policy & prices"
    )
    parser.add_argument(
        "--source",
        type=str,
        default=None,
        help="Scrape only a specific source (e.g., mining_com, lme, rare_earth_cn)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Scrape and clean only, skip DB write. Saves sample to data/",
    )
    args = parser.parse_args()

    run_pipeline(source_filter=args.source, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
