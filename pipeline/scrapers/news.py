"""
RSS-based scrapers for mining news sources.
- Mining.com (RSS feed)
- S&P Global Mining (RSS feed)
"""

import re
from datetime import datetime, timezone
from typing import List, Optional
from xml.etree import ElementTree

import feedparser
import html2text
from bs4 import BeautifulSoup
from loguru import logger

from .base import BaseScraper
from ..config import MIN_ARTICLES_PER_SOURCE, MiningDocument


class MiningComScraper(BaseScraper):
    """Scrape mining.com via RSS feed + full-text extraction."""

    source = "mining_com"
    category = "news"
    language = "en"

    RSS_URL = "https://www.mining.com/feed/"

    def scrape(self) -> List[MiningDocument]:
        logger.info("Scraping Mining.com RSS feed...")
        docs = []

        feed = feedparser.parse(self.RSS_URL)
        entries = feed.entries

        logger.info(f"Mining.com RSS returned {len(entries)} entries")

        for entry in entries[: max(MIN_ARTICLES_PER_SOURCE, 200)]:
            try:
                doc = self._parse_entry(entry)
                if doc:
                    docs.append(doc)
            except Exception as e:
                logger.warning(f"Failed to parse Mining.com entry: {e}")

        logger.info(f"Mining.com: {len(docs)} documents scraped")
        return docs

    def _parse_entry(self, entry) -> Optional[MiningDocument]:
        title = entry.get("title", "").strip()
        link = entry.get("link", "").strip()
        if not title or not link:
            return None

        # Published date
        published = None
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            try:
                published = datetime(
                    *entry.published_parsed[:6], tzinfo=timezone.utc
                ).isoformat()
            except Exception:
                pass

        # Summary / description
        summary = entry.get("summary", "") or entry.get("description", "")
        summary = html2text.html2text(summary) if summary else ""

        # Try to fetch full text
        full_text = self._fetch_full_text(link, summary)

        content = full_text if full_text else summary

        return self._to_doc(
            title=title,
            content=content,
            url=link,
            published_at=published,
            metadata={"rss_summary": summary[:500]},
        )

    def _fetch_full_text(self, url: str, fallback: str = "") -> str:
        """Attempt to extract full article text from the page."""
        try:
            resp = self._get(url)
            soup = BeautifulSoup(resp.text, "lxml")

            # Try common article containers
            for selector in [
                "article",
                ".article-content",
                ".post-content",
                ".entry-content",
                '[itemprop="articleBody"]',
                "main",
            ]:
                container = soup.select_one(selector)
                if container:
                    text = container.get_text(separator="\n", strip=True)
                    if len(text) > 200:
                        return text

            # Fallback: all <p> tags
            paragraphs = soup.find_all("p")
            text = "\n".join(p.get_text(strip=True) for p in paragraphs)
            return text if len(text) > 100 else fallback

        except Exception as e:
            logger.debug(f"Could not fetch full text for {url}: {e}")
            return fallback


class SPGlobalScraper(BaseScraper):
    """Scrape S&P Global Market Intelligence Mining news.

    Primary: RSS feed (if available)
    Fallback: S&P Global Commodity Insights mining news page
    """

    source = "sp_global_mining"
    category = "news"
    language = "en"

    RSS_URL = "https://www.spglobal.com/marketintelligence/en/mi/rss/industry/mining.xml"
    # Fallback URLs if RSS is unavailable
    FALLBACK_URL = "https://www.spglobal.com/commodityinsights/en/markets/metals/mining"

    def scrape(self) -> List[MiningDocument]:
        logger.info("Scraping S&P Global Mining RSS feed...")
        docs = []

        # Try RSS first with a short timeout
        try:
            feed = feedparser.parse(self.RSS_URL)
            entries = feed.entries
            logger.info(f"S&P Global RSS returned {len(entries)} entries")
        except Exception as e:
            logger.warning(f"S&P Global RSS failed: {e}, trying fallback...")
            entries = []

        if not entries:
            # Fallback: scrape the mining news page directly
            logger.info("RSS empty — scraping S&P Global mining news page...")
            docs = self._scrape_fallback()
            logger.info(f"S&P Global fallback: {len(docs)} documents scraped")
            return docs

        for entry in entries[: max(MIN_ARTICLES_PER_SOURCE, 200)]:
            try:
                doc = self._parse_entry(entry)
                if doc:
                    docs.append(doc)
            except Exception as e:
                logger.warning(f"Failed to parse S&P Global entry: {e}")

        logger.info(f"S&P Global Mining: {len(docs)} documents scraped")
        return docs

    def _parse_entry(self, entry) -> Optional[MiningDocument]:
        title = entry.get("title", "").strip()
        link = entry.get("link", "").strip()
        if not title or not link:
            return None

        published = None
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            try:
                published = datetime(
                    *entry.published_parsed[:6], tzinfo=timezone.utc
                ).isoformat()
            except Exception:
                pass

        summary = entry.get("summary", "") or entry.get("description", "")
        summary = html2text.html2text(summary) if summary else ""

        # Try to fetch full article
        full_text = self._fetch_full_text(link)

        content = full_text if full_text and len(full_text) > len(summary) else summary

        return self._to_doc(
            title=title,
            content=content,
            url=link,
            published_at=published,
            metadata={"rss_summary": summary[:500]},
        )

    def _fetch_full_text(self, url: str) -> str:
        """Attempt to extract full article text. S&P may have paywall."""
        try:
            resp = self._get(url)
            soup = BeautifulSoup(resp.text, "lxml")

            for selector in ["article", ".article-body", ".content", "main", ".post"]:
                container = soup.select_one(selector)
                if container:
                    text = container.get_text(separator="\n", strip=True)
                    if len(text) > 200:
                        return text

            paragraphs = soup.find_all("p")
            return "\n".join(p.get_text(strip=True) for p in paragraphs)

        except Exception as e:
            logger.debug(f"Could not fetch S&P full text for {url}: {e}")
            return ""

    def _scrape_fallback(self) -> List[MiningDocument]:
        """Scrape S&P Global Commodity Insights mining page for article links."""
        docs = []
        try:
            resp = self._get(self.FALLBACK_URL)
            soup = BeautifulSoup(resp.text, "lxml")

            links = []
            for a in soup.select("a[href*='/article/'], a[href*='/news/'], .headline a, h3 a, h2 a"):
                href = a.get("href", "")
                title = a.get_text(strip=True)
                if href and len(title) > 10:
                    full_url = href if href.startswith("http") else f"https://www.spglobal.com{href}"
                    if full_url not in [l[0] for l in links]:
                        links.append((full_url, title))

            logger.info(f"Found {len(links)} S&P Global article links")

            for url, title in links[:200]:
                try:
                    text = self._fetch_full_text(url)
                    if len(text) > 50:
                        docs.append(self._to_doc(
                            title=title,
                            content=text,
                            url=url,
                        ))
                except Exception as e:
                    logger.debug(f"Failed S&P article {url}: {e}")

        except Exception as e:
            logger.warning(f"S&P Global fallback scrape failed: {e}")

        return docs
