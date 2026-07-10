"""
Lightweight vector store + embedder using pure-Python TF-IDF + numpy.
Zero heavy dependencies — works with just Python stdlib + numpy.

This is the MVP backend. For production with better semantic search,
install chromadb + sentence-transformers and use vector_store.py + embedder.py.
"""

import json
import math
import pickle
from collections import Counter
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np
from loguru import logger

from .config import DATA_DIR, MiningDocument


class SimpleTfidfVectorizer:
    """
    Pure-Python TF-IDF with character n-grams (works for zh + en).
    No sklearn dependency.
    """

    def __init__(self, max_features: int = 1024, ngram_range: tuple = (1, 3)):
        self.max_features = max_features
        self.ngram_range = ngram_range
        self.vocabulary_: Dict[str, int] = {}
        self.idf_: np.ndarray = None

    @staticmethod
    def _char_ngrams(text: str, n_min: int, n_max: int) -> List[str]:
        """Extract character n-grams from text."""
        # Normalize: keep CJK chars, letters, digits, collapse whitespace
        chars = []
        for ch in text.lower():
            if ch.isspace():
                chars.append(" ")
            elif ch.isalnum() or '一' <= ch <= '鿿' or '㐀' <= ch <= '䶿':
                chars.append(ch)
            else:
                chars.append(" ")  # Replace punctuation with space
        text = "".join(chars)
        # Split by whitespace and filter
        words = text.split()
        text_compact = "".join(words)

        ngrams = []
        # Word-level bigrams for English
        for i in range(len(words) - 1):
            ngrams.append(f"W_{words[i]}_{words[i+1]}")

        # Character n-grams for mixed language
        for n in range(n_min, n_max + 1):
            for i in range(len(text_compact) - n + 1):
                ngrams.append(text_compact[i:i + n])

        return ngrams

    def fit(self, texts: List[str]):
        """Fit TF-IDF on a corpus of texts."""
        # Count document frequency for each n-gram
        df = Counter()
        total_ngrams = Counter()

        for text in texts:
            ngrams = set(self._char_ngrams(text, *self.ngram_range))
            for ng in ngrams:
                df[ng] += 1
                total_ngrams[ng] += 1

        # Select top max_features by document frequency
        top_ngrams = df.most_common(self.max_features)
        self.vocabulary_ = {ng: i for i, (ng, _) in enumerate(top_ngrams)}

        # Compute IDF
        n_docs = len(texts)
        self.idf_ = np.zeros(len(self.vocabulary_))
        for ng, idx in self.vocabulary_.items():
            self.idf_[idx] = math.log((1 + n_docs) / (1 + df.get(ng, 0))) + 1

        logger.info(f"SimpleTfidfVectorizer fitted: vocab={len(self.vocabulary_)}")

    def transform(self, texts: List[str]) -> np.ndarray:
        """Transform texts to TF-IDF vectors."""
        n_docs = len(texts)
        result = np.zeros((n_docs, len(self.vocabulary_)))

        for i, text in enumerate(texts):
            ngrams = self._char_ngrams(text, *self.ngram_range)
            tf = Counter(ngrams)
            for ng, count in tf.items():
                if ng in self.vocabulary_:
                    idx = self.vocabulary_[ng]
                    # Sublinear TF scaling
                    result[i, idx] = (1 + math.log(count)) * self.idf_[idx]

            # L2 normalize per document
            norm = np.linalg.norm(result[i])
            if norm > 0:
                result[i] /= norm

        return result

    def fit_transform(self, texts: List[str]) -> np.ndarray:
        self.fit(texts)
        return self.transform(texts)


class LightweightEmbedder:
    """TF-IDF based embedder using SimpleTfidfVectorizer."""

    def __init__(self):
        self.vectorizer = SimpleTfidfVectorizer(max_features=1024)
        self._fitted = False

    def fit_transform(self, docs: List[MiningDocument]) -> np.ndarray:
        texts = [self._to_text(d) for d in docs]
        embeddings = self.vectorizer.fit_transform(texts)
        self._fitted = True
        return embeddings

    def transform(self, docs: List[MiningDocument]) -> np.ndarray:
        texts = [self._to_text(d) for d in docs]
        return self.vectorizer.transform(texts)

    def embed_query(self, query: str, source_prefix: str = "") -> np.ndarray:
        if source_prefix:
            query = f"{source_prefix} {query}"
        vec = self.vectorizer.transform([query])
        return vec[0]

    @staticmethod
    def _to_text(doc: MiningDocument) -> str:
        prefix = f"[{doc.source}] [{doc.category}]"
        return f"{prefix} {doc.title} {doc.content[:2000]}"


class LightweightVectorStore:
    """
    Simple vector store backed by numpy arrays + JSON metadata.

    Stores:
    - embeddings.npy — float32 matrix (N, dim)
    - metadata.json — list of {id, source, category, title, url, ...}
    - tfidf.pkl — fitted TfidfVectorizer state
    """

    def __init__(self, store_dir: Path = None):
        self.store_dir = store_dir or DATA_DIR / "lightweight_store"
        self.store_dir.mkdir(parents=True, exist_ok=True)

        self.embeddings: Optional[np.ndarray] = None
        self.metadata: List[Dict[str, Any]] = []
        self.embedder: Optional[LightweightEmbedder] = None

        self._load()

    def _load(self):
        emb_path = self.store_dir / "embeddings.npy"
        meta_path = self.store_dir / "metadata.json"
        tfidf_path = self.store_dir / "tfidf.pkl"

        if emb_path.exists() and meta_path.exists():
            self.embeddings = np.load(emb_path)
            with open(meta_path, "r", encoding="utf-8") as f:
                self.metadata = json.load(f)
            logger.info(f"Loaded {len(self.metadata)} docs from lightweight store")

        if tfidf_path.exists():
            with open(tfidf_path, "rb") as f:
                self.embedder = LightweightEmbedder()
                self.embedder.vectorizer = pickle.load(f)
                self.embedder._fitted = True
            logger.info("Loaded TF-IDF vectorizer state")

    def _save(self):
        if self.embeddings is not None:
            np.save(self.store_dir / "embeddings.npy", self.embeddings)
        with open(self.store_dir / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)
        if self.embedder and self.embedder._fitted:
            with open(self.store_dir / "tfidf.pkl", "wb") as f:
                pickle.dump(self.embedder.vectorizer, f)

    def add_documents(
        self, docs: List[MiningDocument], embeddings: np.ndarray = None,
        embedder: LightweightEmbedder = None
    ) -> int:
        """
        Add documents with optional pre-computed embeddings.
        If embeddings not provided, fits TF-IDF on all docs.
        Pass embedder to persist its state for later query use.
        """
        if embedder is not None:
            self.embedder = embedder

        if embeddings is not None:
            self.embeddings = embeddings
        else:
            if self.embedder is None:
                self.embedder = LightweightEmbedder()
            self.embeddings = self.embedder.fit_transform(docs)

        self.metadata = [
            {
                "id": d.id,
                "source": d.source,
                "category": d.category,
                "title": d.title,
                "url": d.url,
                "language": d.language,
                "published_at": d.published_at or "",
                "content_preview": (d.content or "")[:500],
                "minerals": d.metadata.get("minerals_mentioned", []),
                "policy_types": d.metadata.get("policy_types", []),
                "ingested_at": d.ingested_at or "",
            }
            for d in docs
        ]

        self._save()
        logger.info(f"Lightweight store: saved {len(docs)} documents")
        return len(docs)

    def search(
        self,
        query_embedding: np.ndarray,
        n_results: int = 5,
        source_filter: str = None,
        category_filter: str = None,
        days_filter: int = None,
    ) -> List[Dict[str, Any]]:
        """Cosine similarity search."""
        if self.embeddings is None or len(self.metadata) == 0:
            return []

        # Compute cosine similarity (embeddings are already normalized)
        scores = self.embeddings @ query_embedding

        # Get top-k indices
        top_indices = np.argsort(scores)[::-1]

        results = []
        for idx in top_indices:
            if len(results) >= n_results:
                break

            meta = self.metadata[idx]

            # Apply filters
            if source_filter and meta["source"] != source_filter:
                continue
            if category_filter and meta["category"] != category_filter:
                continue
            if days_filter and meta.get("published_at"):
                from datetime import datetime, timezone, timedelta
                try:
                    pub_date = datetime.fromisoformat(
                        meta["published_at"].replace("Z", "+00:00")
                    )
                    cutoff = datetime.now(timezone.utc) - timedelta(days=days_filter)
                    if pub_date < cutoff:
                        continue
                except Exception:
                    pass

            results.append(
                {
                    "id": meta["id"],
                    "content": f"{meta['title']}\n\n{meta.get('content_preview', '')}",
                    "metadata": meta,
                    "distance": float(1.0 - scores[idx]),
                    "relevance": float(scores[idx]),
                }
            )

        return results

    def count(self) -> int:
        return len(self.metadata)

    def get_stats(self) -> Dict[str, Any]:
        by_source = {}
        by_category = {}
        for m in self.metadata:
            src = m.get("source", "unknown")
            cat = m.get("category", "unknown")
            by_source[src] = by_source.get(src, 0) + 1
            by_category[cat] = by_category.get(cat, 0) + 1

        return {
            "total": len(self.metadata),
            "by_source": by_source,
            "by_category": by_category,
        }
