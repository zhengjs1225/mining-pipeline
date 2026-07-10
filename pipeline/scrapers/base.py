"""
Base scraper with retry logic, rate-limiting, and structured output.
"""

import hashlib
import random
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import List, Optional

import httpx
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import (
    MAX_RETRIES,
    REQUEST_TIMEOUT,
    RETRY_DELAY,
    USER_AGENTS,
    MiningDocument,
)


class BaseScraper(ABC):
    """Abstract base for all source scrapers."""

    source: str
    category: str
    language: str = "en"

    def __init__(self):
        self._client: Optional[httpx.Client] = None

    @property
    def client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(
                timeout=REQUEST_TIMEOUT,
                headers=self._default_headers(),
                follow_redirects=True,
            )
        return self._client

    def _default_headers(self) -> dict:
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }

    def _rotate_ua(self):
        """Rotate User-Agent to avoid detection."""
        self.client.headers["User-Agent"] = random.choice(USER_AGENTS)

    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=RETRY_DELAY, max=30),
    )
    def _get(self, url: str, **kwargs) -> httpx.Response:
        """GET with retry + exponential backoff."""
        self._rotate_ua()
        logger.debug(f"GET {url}")
        resp = self.client.get(url, **kwargs)
        resp.raise_for_status()
        return resp

    def _make_id(self, url: str) -> str:
        """Deterministic primary key: SHA256(source + url)."""
        raw = f"{self.source}:{url}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _to_doc(
        self,
        title: str,
        content: str,
        url: str,
        published_at: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> MiningDocument:
        """Build a unified MiningDocument."""
        return MiningDocument(
            id=self._make_id(url),
            source=self.source,
            category=self.category,
            title=title,
            content=content,
            url=url,
            published_at=published_at,
            language=self.language,
            metadata=metadata or {},
            ingested_at=self._now_iso(),
        )

    @abstractmethod
    def scrape(self) -> List[MiningDocument]:
        """Fetch articles/records. Returns list of MiningDocument."""
        ...

    def close(self):
        if self._client:
            self._client.close()
            self._client = None
