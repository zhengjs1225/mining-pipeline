"""
HTML-based scrapers for critical mineral policy sources.
- 中国稀土集团 (China Rare Earth Group) — policy/news pages
- Australia DISR Critical Minerals Strategy
"""

import re
from datetime import datetime, timezone
from typing import List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from loguru import logger

from .base import BaseScraper
from ..config import MIN_ARTICLES_PER_SOURCE, MiningDocument


class RareEarthCNScraper(BaseScraper):
    """
    Scrape 中国稀土集团 (China Rare Earth Group) policy/news pages.

    The site structure:
    - /xwzx/jtyw/ — 集团要闻 (Group News)
    - /xwzx/gsdt/ — 公司动态 (Company Updates)
    - policy-related content about rare earth production, export quotas, etc.

    Anti-scraping: moderate. We use delays, UA rotation, and parse
    the listing pages then individual articles.
    """

    source = "rare_earth_cn"
    category = "policy"
    language = "zh"

    BASE_URL = "https://www.creg.com.cn"
    LIST_PAGES = [
        "/xwzx/jtyw/",   # 集团要闻
        "/xwzx/gsdt/",   # 公司动态
    ]

    def scrape(self) -> List[MiningDocument]:
        logger.info("Scraping 中国稀土集团 policy pages...")
        docs = []

        for list_path in self.LIST_PAGES:
            list_url = urljoin(self.BASE_URL, list_path)
            try:
                article_urls = self._get_article_urls(list_url)
                logger.info(f"Found {len(article_urls)} article URLs from {list_path}")

                for article_url in article_urls[: max(MIN_ARTICLES_PER_SOURCE // 2, 100)]:
                    try:
                        doc = self._parse_article(article_url)
                        if doc:
                            docs.append(doc)
                    except Exception as e:
                        logger.warning(f"Failed to parse article {article_url}: {e}")
            except Exception as e:
                logger.error(f"Failed to scrape list page {list_url}: {e}")

        logger.info(f"中国稀土集团: {len(docs)} documents scraped")
        return docs

    def _get_article_urls(self, list_url: str) -> List[str]:
        """Extract article links from a listing page."""
        try:
            resp = self._get(list_url)
            resp.encoding = "utf-8"
            soup = BeautifulSoup(resp.text, "lxml")

            links = []
            # Common Chinese gov/corp news site patterns
            for a in soup.select(
                "a[href*='content'], a[href*='info'], a[href*='detail'], "
                ".news-list a, .article-list a, .list-item a, li a"
            ):
                href = a.get("href", "")
                if href and any(
                    kw in href for kw in ["content", "info", "detail", "art_", "id="]
                ):
                    full_url = urljoin(self.BASE_URL, href)
                    if full_url not in links:
                        links.append(full_url)

            # Fallback: collect all internal links with sufficient path depth
            if not links:
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    if href.startswith("/") and len(href.split("/")) > 3:
                        full_url = urljoin(self.BASE_URL, href)
                        if full_url not in links and self.BASE_URL in full_url:
                            links.append(full_url)

            return links

        except Exception as e:
            logger.error(f"Error getting article URLs from {list_url}: {e}")
            return []

    def _parse_article(self, url: str) -> Optional[MiningDocument]:
        """Parse a single article page."""
        try:
            resp = self._get(url)
            resp.encoding = "utf-8"
            soup = BeautifulSoup(resp.text, "lxml")

            # Title
            title = None
            for tag in ["h1", "h2", ".article-title", ".news-title", ".content-title"]:
                el = soup.select_one(tag)
                if el:
                    title = el.get_text(strip=True)
                    if title:
                        break
            if not title:
                title = soup.title.string if soup.title else "Untitled"

            # Date
            published_at = None
            date_patterns = [
                r"(\d{4}[-/]\d{2}[-/]\d{2})",
                r"(\d{4}年\d{1,2}月\d{1,2}日)",
            ]
            page_text = soup.get_text()
            for pat in date_patterns:
                m = re.search(pat, page_text)
                if m:
                    date_str = m.group(1)
                    try:
                        date_str = date_str.replace("年", "-").replace("月", "-").replace("日", "")
                        published_at = datetime.strptime(
                            date_str.replace("/", "-"), "%Y-%m-%d"
                        ).replace(tzinfo=timezone.utc).isoformat()
                    except Exception:
                        pass
                    break

            # Content
            content_parts = []
            for selector in [
                ".article-content", ".news-content", ".content-body",
                ".TRS_Editor", "#article-content", "article",
            ]:
                container = soup.select_one(selector)
                if container:
                    content_parts.append(
                        container.get_text(separator="\n", strip=True)
                    )

            if not content_parts:
                # Fallback: all paragraphs
                for p in soup.find_all("p"):
                    text = p.get_text(strip=True)
                    if len(text) > 20:
                        content_parts.append(text)

            content = "\n\n".join(content_parts)

            if len(content) < 50:
                return None

            # Extract policy-related metadata
            metadata = self._extract_policy_metadata(content, title)

            return self._to_doc(
                title=title.strip(),
                content=content,
                url=url,
                published_at=published_at,
                metadata=metadata,
            )

        except Exception as e:
            logger.warning(f"Error parsing article {url}: {e}")
            return None

    def _extract_policy_metadata(self, content: str, title: str) -> dict:
        """Extract policy-specific metadata like minerals mentioned, policy type."""
        metadata = {}

        # Detect mentioned minerals
        minerals = [
            "稀土", "锂", "钴", "镍", "铜", "锌", "铁矿石",
            "rare earth", "lithium", "cobalt", "nickel", "copper",
            "钨", "锑", "锗", "镓", "钒", "钛",
        ]
        mentioned = [m for m in minerals if m in content or m in title]
        metadata["minerals_mentioned"] = mentioned

        # Policy type detection
        policy_keywords = {
            "export_quota": ["出口配额", "出口管制", "export quota"],
            "production_cap": ["产量上限", "生产指标", "production cap"],
            "environmental": ["环保", "环境", "environmental", "ESG"],
            "subsidy": ["补贴", "扶持", "subsidy", "incentive"],
            "strategic_reserve": ["储备", "战略", "strategic reserve"],
            "trade_restriction": ["关税", "限制", "禁令", "ban", "restriction"],
        }
        detected = []
        for ptype, keywords in policy_keywords.items():
            if any(kw in content.lower() or kw in title.lower() for kw in keywords):
                detected.append(ptype)
        metadata["policy_types"] = detected

        return metadata


class DISRAUScraper(BaseScraper):
    """
    Scrape Australia DISR Critical Minerals Strategy & related publications.

    Source: https://www.industry.gov.au/publications/australias-critical-minerals-strategy

    Strategy: fetch the main strategy page + related publications listing,
    then extract full text from PDF-links and HTML pages.
    """

    source = "disr_au"
    category = "policy"
    language = "en"

    BASE_URL = "https://www.industry.gov.au"
    STRATEGY_URL = (
        "https://www.industry.gov.au/publications/"
        "australias-critical-minerals-strategy"
    )
    RELATED_URLS = [
        "https://www.industry.gov.au/publications/critical-minerals-strategy-2023-2030",
        "https://www.industry.gov.au/mining-oil-and-gas/critical-minerals",
    ]

    def scrape(self) -> List[MiningDocument]:
        logger.info("Scraping Australia DISR Critical Minerals Strategy...")
        docs = []

        # Main strategy page
        try:
            doc = self._parse_page(self.STRATEGY_URL)
            if doc:
                docs.append(doc)
        except Exception as e:
            logger.error(f"Failed to parse main DISR page: {e}")

        # Related pages
        for url in self.RELATED_URLS:
            try:
                doc = self._parse_page(url)
                if doc:
                    docs.append(doc)
            except Exception as e:
                logger.warning(f"Failed to parse DISR related page {url}: {e}")

        # Also try to fetch listing of all critical minerals publications
        try:
            listing_docs = self._scrape_publications_listing()
            docs.extend(listing_docs)
        except Exception as e:
            logger.warning(f"Failed to scrape DISR publications listing: {e}")

        logger.info(f"Australia DISR: {len(docs)} documents scraped")
        return docs

    def _parse_page(self, url: str) -> Optional[MiningDocument]:
        """Parse a single DISR HTML page."""
        try:
            resp = self._get(url)
            soup = BeautifulSoup(resp.text, "lxml")

            title = None
            for tag in ["h1", ".page-title", ".document-title", "title"]:
                el = soup.select_one(tag)
                if el:
                    title = el.get_text(strip=True)
                    if len(title) > 10:
                        break
            if not title:
                title = soup.title.string if soup.title else "Australia Critical Minerals"

            # Date
            published_at = None
            date_el = soup.select_one(
                ".published-date, .date, .publish-date, time, [datetime]"
            )
            if date_el:
                date_str = date_el.get("datetime") or date_el.get_text(strip=True)
                try:
                    published_at = datetime.fromisoformat(
                        date_str.replace("Z", "+00:00")
                    ).isoformat()
                except Exception:
                    pass

            if not published_at:
                # Try regex on page text
                text = soup.get_text()
                m = re.search(r"(\d{1,2}\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})", text)
                if m:
                    try:
                        published_at = datetime.strptime(
                            m.group(1), "%d %B %Y"
                        ).replace(tzinfo=timezone.utc).isoformat()
                    except Exception:
                        pass

            # Content
            main_content = soup.select_one(
                "main, article, .content, .page-content, #content, .main-content"
            )
            if main_content:
                content = main_content.get_text(separator="\n", strip=True)
            else:
                paragraphs = soup.find_all("p")
                content = "\n".join(p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 20)

            if len(content) < 100:
                return None

            # Extract metadata
            metadata = self._extract_metadata(content, title)

            return self._to_doc(
                title=title.strip(),
                content=content,
                url=url,
                published_at=published_at,
                metadata=metadata,
            )

        except Exception as e:
            logger.warning(f"Error parsing DISR page {url}: {e}")
            return None

    def _scrape_publications_listing(self) -> List[MiningDocument]:
        """Scrape the publications listing pages for more documents."""
        docs = []
        listing_url = (
            "https://www.industry.gov.au/mining-oil-and-gas/critical-minerals"
        )

        try:
            resp = self._get(listing_url)
            soup = BeautifulSoup(resp.text, "lxml")

            # Find publication links
            links_seen = set()
            for a in soup.select(
                "a[href*='publication'], a[href*='critical-mineral'], "
                "a[href*='strategy'], .listing a, .publications a"
            ):
                href = a.get("href", "")
                if href and "critical-mineral" in href.lower():
                    full_url = urljoin(self.BASE_URL, href)
                    if full_url not in links_seen:
                        links_seen.add(full_url)

            # Parse each linked publication
            for url in list(links_seen)[:50]:
                try:
                    doc = self._parse_page(url)
                    if doc:
                        docs.append(doc)
                except Exception:
                    pass

        except Exception as e:
            logger.warning(f"Error scraping DISR publications listing: {e}")

        return docs

    def _extract_metadata(self, content: str, title: str) -> dict:
        """Extract policy metadata."""
        metadata = {}

        minerals = [
            "lithium", "cobalt", "nickel", "copper", "zinc",
            "rare earth", "rare-earth", "graphite", "vanadium",
            "titanium", "tungsten", "antimony", "germanium",
            "gallium", "manganese", "chromium", "platinum",
        ]
        mentioned = [m for m in minerals if m.lower() in content.lower() or m.lower() in title.lower()]
        metadata["minerals_mentioned"] = mentioned

        policy_keywords = {
            "export_control": ["export control", "export restriction", "export ban"],
            "investment": ["investment", "funding", "grant", "incentive"],
            "environmental": ["environmental", "ESG", "sustainability", "net zero"],
            "indigenous": ["indigenous", "first nations", "traditional owner"],
            "processing": ["processing", "refining", "downstream", "value adding"],
            "supply_chain": ["supply chain", "diversification", "resilience"],
        }
        detected = []
        for ptype, keywords in policy_keywords.items():
            if any(kw in content.lower() for kw in keywords):
                detected.append(ptype)
        metadata["policy_types"] = detected

        return metadata
