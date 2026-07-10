"""
Deduplication strategies for mining documents.

Strategies:
1. Exact ID dedup — SHA256(source + url), handled at scrape time
2. Content fingerprint — SimHash / MD5 of normalized content
3. Near-duplicate detection — Jaccard similarity on bigrams (Chinese + English)
"""

import hashlib
import re
from typing import List, Set, Tuple

from loguru import logger

from .config import MiningDocument


class Deduplicator:
    """
    Multi-strategy deduplication for mining documents.

    Primary key: SHA256(source + url) — exact duplicate prevention.
    Content fingerprint: MD5(normalized content) — catches same article from different URLs.
    Near-duplicate: Jaccard on word bigrams — catches slightly edited re-posts.
    """

    JACCARD_THRESHOLD = 0.85  # Consider as duplicate if Jaccard >= 85%

    def __init__(self):
        self._seen_ids: Set[str] = set()
        self._seen_fingerprints: Set[str] = set()
        self._bigram_sets: List[Tuple[str, Set[str]]] = []  # (doc_id, bigram_set)

    def deduplicate(self, docs: List[MiningDocument]) -> List[MiningDocument]:
        """
        Apply all dedup strategies. Returns unique documents.
        Order preserved — first occurrence kept.
        """
        # Stage 1: Exact ID dedup
        stage1 = self._dedup_by_id(docs)
        logger.debug(f"Dedup stage 1 (ID): {len(docs)} → {len(stage1)}")

        # Stage 2: Content fingerprint dedup
        stage2 = self._dedup_by_fingerprint(stage1)
        logger.debug(f"Dedup stage 2 (fingerprint): {len(stage1)} → {len(stage2)}")

        # Stage 3: Near-duplicate detection
        stage3 = self._dedup_near_duplicates(stage2)
        logger.debug(f"Dedup stage 3 (near-dup): {len(stage2)} → {len(stage3)}")

        total_removed = len(docs) - len(stage3)
        logger.info(
            f"Deduplication: {len(docs)} → {len(stage3)} documents "
            f"({total_removed} duplicates removed)"
        )
        return stage3

    def _dedup_by_id(self, docs: List[MiningDocument]) -> List[MiningDocument]:
        """Remove exact ID duplicates."""
        result = []
        for doc in docs:
            if doc.id not in self._seen_ids:
                self._seen_ids.add(doc.id)
                result.append(doc)
        return result

    def _dedup_by_fingerprint(self, docs: List[MiningDocument]) -> List[MiningDocument]:
        """Remove documents with identical normalized content."""
        result = []
        for doc in docs:
            fp = self._content_fingerprint(doc)
            if fp not in self._seen_fingerprints:
                self._seen_fingerprints.add(fp)
                result.append(doc)
        return result

    def _dedup_near_duplicates(
        self, docs: List[MiningDocument]
    ) -> List[MiningDocument]:
        """Remove near-duplicate documents using Jaccard similarity on bigrams.

        Price documents are excluded: they use a fixed template with varying
        numeric data, so bigram similarity is inherently high (~1.0) even
        though each document represents distinct daily data points.
        """
        result = []
        for doc in docs:
            # Skip near-duplicate check for price documents — each day's
            # price data is distinct information despite structural similarity.
            if doc.category == "price":
                result.append(doc)
                continue

            bigrams = self._extract_bigrams(doc)

            is_dup = False
            for _, existing_bigrams in self._bigram_sets:
                jaccard = self._jaccard(bigrams, existing_bigrams)
                if jaccard >= self.JACCARD_THRESHOLD:
                    is_dup = True
                    logger.debug(
                        f"Near-duplicate detected: '{doc.title[:60]}' "
                        f"(Jaccard={jaccard:.3f})"
                    )
                    break

            if not is_dup:
                self._bigram_sets.append((doc.id, bigrams))
                result.append(doc)

        return result

    @staticmethod
    def _content_fingerprint(doc: MiningDocument) -> str:
        """MD5 hash of normalized content (first 2000 chars)."""
        normalized = doc.content.lower().strip()
        normalized = re.sub(r"\s+", " ", normalized)  # Collapse all whitespace
        normalized = re.sub(r"[^\w\s]", "", normalized)  # Remove punctuation
        normalized = normalized[:2000]  # First 2000 chars
        return hashlib.md5(normalized.encode("utf-8")).hexdigest()

    @staticmethod
    def _extract_bigrams(doc: MiningDocument) -> Set[str]:
        """Extract word bigrams from document content.

        For Chinese: character bigrams (since words are not space-separated).
        For English: word bigrams.
        """
        content = doc.content.strip()

        if doc.language == "zh":
            # Chinese: character bigrams
            # Remove spaces, punctuation, ASCII for Chinese text
            chars = re.sub(r"[\s\w\d" + re.escape("!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~，。！？；：""''（）【】《》…—·") + "]", "", content)
            bigrams = set()
            for i in range(len(chars) - 1):
                bigrams.add(chars[i : i + 2])
            return bigrams
        else:
            # English: word bigrams
            words = re.findall(r"[a-zA-Z]+", content.lower())
            words = [w for w in words if len(w) > 2]  # Skip short words
            bigrams = set()
            for i in range(len(words) - 1):
                bigrams.add(f"{words[i]}_{words[i+1]}")
            return bigrams

    @staticmethod
    def _jaccard(set_a: Set[str], set_b: Set[str]) -> float:
        """Jaccard similarity between two sets."""
        if not set_a or not set_b:
            return 0.0
        intersection = len(set_a & set_b)
        union = len(set_a | set_b)
        return intersection / union if union > 0 else 0.0
