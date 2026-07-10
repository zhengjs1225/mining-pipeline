"""
Shared configuration for the mining data pipeline.
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

# Load .env file if present
_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"
if _ENV_FILE.exists():
    with open(_ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                key, val = key.strip(), val.strip().strip('"').strip("'")
                if key not in os.environ:
                    os.environ[key] = val

# Project root
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
CHROMA_DIR = DATA_DIR / "chroma"

# Ensure data dirs exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

# ── Embedding ──────────────────────────────────────────────
EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "BAAI/bge-m3"  # Multilingual, supports Chinese + English, 1024-dim
)
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "1024"))

# ── LLM (for answer generation) ────────────────────────────
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")

# ── ChromaDB ───────────────────────────────────────────────
CHROMA_COLLECTION = "mining_docs"

# ── Scraping ───────────────────────────────────────────────
SCRAPE_DAYS = int(os.getenv("SCRAPE_DAYS", "30"))  # At least 30 days
MIN_ARTICLES_PER_SOURCE = int(os.getenv("MIN_ARTICLES_PER_SOURCE", "200"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))  # 30s per request
RSS_TIMEOUT = int(os.getenv("RSS_TIMEOUT", "15"))  # Short timeout for RSS feeds
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "2"))  # 1 retry = 2 attempts max
RETRY_DELAY = float(os.getenv("RETRY_DELAY", "2.0"))

# User-Agent rotation
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]

# ── Data Schema ────────────────────────────────────────────
@dataclass
class MiningDocument:
    """Unified schema for all ingested mining documents."""
    id: str                          # SHA256 hash of (source + url) — deterministic primary key
    source: str                      # "mining_com" | "sp_global" | "rare_earth_cn" | "disr_au" | "lme" | "shfe" | "steel_union"
    category: str                    # "news" | "policy" | "price"
    title: str
    content: str                     # Full text or structured summary
    url: str
    published_at: Optional[str] = None  # ISO 8601
    language: str = "zh"             # "zh" | "en"
    metadata: dict = field(default_factory=dict)  # source-specific extras (price values, tickers, etc.)
    ingested_at: Optional[str] = None  # ISO 8601 — when we pulled it


# ── Source URLs ────────────────────────────────────────────
SOURCES = {
    "mining_com": {
        "name": "Mining.com",
        "rss": "https://www.mining.com/feed/",
        "category": "news",
        "language": "en",
    },
    "sp_global_mining": {
        "name": "S&P Global Mining",
        "rss": "https://www.spglobal.com/marketintelligence/en/mi/rss/industry/mining.xml",
        "category": "news",
        "language": "en",
    },
    "rare_earth_cn": {
        "name": "中国稀土集团",
        "base_url": "https://www.creg.com.cn",
        "news_url": "https://www.creg.com.cn/xwzx/jtyw/",
        "category": "policy",
        "language": "zh",
    },
    "disr_au": {
        "name": "Australia DISR Critical Minerals",
        "base_url": "https://www.industry.gov.au",
        "url": "https://www.industry.gov.au/publications/australias-critical-minerals-strategy",
        "category": "policy",
        "language": "en",
    },
    "lme": {
        "name": "LME Prices",
        "base_url": "https://www.lme.com",
        "url": "https://www.lme.com/en/metals/non-ferrous/lme-copper",
        "category": "price",
        "language": "en",
        "tickers": ["copper", "zinc", "nickel"],
    },
    "shfe": {
        "name": "SHFE Lithium",
        "base_url": "https://www.shfe.com.cn",
        "category": "price",
        "language": "zh",
        "tickers": ["lithium"],
    },
    "steel_union": {
        "name": "上海钢联 (Mysteel)",
        "base_url": "https://www.mysteel.com",
        "category": "price",
        "language": "zh",
        "tickers": ["iron_ore"],
    },
}
