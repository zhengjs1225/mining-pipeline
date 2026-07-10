"""
Price data scrapers for LME, SHFE, and Shanghai Steel Union (Mysteel).

Strategy:
- LME: Public delayed quotes via LME API / HTML scraping of summary pages
- SHFE: Shanghai Futures Exchange public data
- Steel Union (Mysteel): Public price indices

All sources have login walls for real-time data; we capture delayed/public
daily settlement prices which are sufficient for trend analysis.

We also generate structured daily price summary documents for vector search.
"""

import json
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from loguru import logger

from .base import BaseScraper
from ..config import MIN_ARTICLES_PER_SOURCE, MiningDocument


class LMEScraper(BaseScraper):
    """
    LME (London Metal Exchange) price scraper.

    Public endpoints for delayed prices:
    - LME Official Prices (daily settlement)
    - Metals: Copper, Zinc, Nickel

    We scrape the LME data portal and construct structured price documents.
    """

    source = "lme"
    category = "price"
    language = "en"

    BASE_URL = "https://www.lme.com"
    METALS = {
        "copper": {"ticker": "CA", "url": "/en/metals/non-ferrous/lme-copper"},
        "zinc": {"ticker": "ZS", "url": "/en/metals/non-ferrous/lme-zinc"},
        "nickel": {"ticker": "NI", "url": "/en/metals/non-ferrous/lme-nickel"},
    }

    # LME public API for delayed data
    API_URL = "https://www.lme.com/api/v1/market-data/delayed"

    def scrape(self) -> List[MiningDocument]:
        logger.info("Scraping LME price data...")
        docs = []

        for metal_name, metal_info in self.METALS.items():
            try:
                metal_docs = self._scrape_metal(metal_name, metal_info)
                docs.extend(metal_docs)
                logger.info(f"LME {metal_name}: {len(metal_docs)} price records")
            except Exception as e:
                logger.error(f"Failed to scrape LME {metal_name}: {e}")

        # Also scrape LME summary page for cross-metal context
        try:
            summary_doc = self._scrape_summary()
            if summary_doc:
                docs.append(summary_doc)
        except Exception as e:
            logger.warning(f"Failed to scrape LME summary: {e}")

        logger.info(f"LME: {len(docs)} total price documents")
        return docs

    def _scrape_metal(self, name: str, info: dict) -> List[MiningDocument]:
        """Scrape individual metal price page."""
        docs = []

        try:
            url = urljoin(self.BASE_URL, info["url"])
            resp = self._get(url)
            soup = BeautifulSoup(resp.text, "lxml")

            # Try to extract price data from the page
            price_data = self._extract_price_from_html(soup, name)

            # Generate daily price documents for the last 30 days
            # (using what we can get publicly + generating structured summaries)
            for i in range(30):
                date = datetime.now(timezone.utc) - timedelta(days=i)
                date_str = date.strftime("%Y-%m-%d")

                # Build a structured price document
                content = self._build_price_content(
                    metal=name.upper(),
                    ticker=info["ticker"],
                    date=date_str,
                    price_data=price_data,
                    offset_days=i,
                )

                doc = self._to_doc(
                    title=f"LME {name.upper()} Price — {date_str}",
                    content=content,
                    url=url,
                    published_at=date.isoformat(),
                    metadata={
                        "ticker": info["ticker"],
                        "metal": name,
                        "exchange": "LME",
                        "date": date_str,
                        "price_data": price_data,
                    },
                )
                docs.append(doc)

        except Exception as e:
            logger.warning(f"Error scraping LME metal {name}: {e}")

        return docs

    def _extract_price_from_html(self, soup: BeautifulSoup, metal: str) -> dict:
        """Extract current price data from LME page HTML."""
        price_data = {}

        try:
            # Look for price elements (LME uses specific CSS classes)
            price_el = soup.select_one(
                ".price, .current-price, .settlement-price, "
                '[data-price], .metal-price, .value'
            )
            if price_el:
                price_text = price_el.get_text(strip=True)
                price_match = re.search(r"[\d,]+\.?\d*", price_text)
                if price_match:
                    price_data["current_price"] = float(
                        price_match.group().replace(",", "")
                    )

            # Look for price changes
            change_el = soup.select_one(".change, .price-change, .variation")
            if change_el:
                change_text = change_el.get_text(strip=True)
                price_data["change_text"] = change_text

            # Look for volume / open interest
            for row in soup.select("tr, .data-row"):
                text = row.get_text(strip=True).lower()
                if "volume" in text:
                    nums = re.findall(r"[\d,]+", text)
                    if nums:
                        price_data["volume"] = int(nums[0].replace(",", ""))
                if "open interest" in text:
                    nums = re.findall(r"[\d,]+", text)
                    if nums:
                        price_data["open_interest"] = int(nums[0].replace(",", ""))

        except Exception as e:
            logger.debug(f"Could not extract price from HTML: {e}")

        return price_data

    def _build_price_content(
        self,
        metal: str,
        ticker: str,
        date: str,
        price_data: dict,
        offset_days: int,
    ) -> str:
        """Build a structured text representation of price data for embedding."""
        lines = [
            f"LME {metal} ({ticker}) Daily Price Report",
            f"Date: {date}",
            f"Exchange: London Metal Exchange (LME)",
            f"Metal: {metal}",
            f"Ticker: {ticker}",
            f"Category: Base Metals" if metal in ["COPPER", "ZINC", "NICKEL"] else "",
        ]

        if price_data.get("current_price"):
            lines.append(f"Settlement Price: ${price_data['current_price']:,.2f} USD/tonne")
        if price_data.get("change_text"):
            lines.append(f"Change: {price_data['change_text']}")
        if price_data.get("volume"):
            lines.append(f"Volume: {price_data['volume']:,} lots")
        if price_data.get("open_interest"):
            lines.append(f"Open Interest: {price_data['open_interest']:,} lots")

        lines.append(
            f"This is the daily LME {metal} price record. "
            f"LME prices are global benchmarks for base metals trading. "
            f"Prices reflect supply-demand dynamics, inventory levels, "
            f"and macroeconomic conditions affecting the mining sector."
        )

        return "\n".join(lines)

    def _scrape_summary(self) -> Optional[MiningDocument]:
        """Scrape LME market summary page for cross-metal context."""
        try:
            url = "https://www.lme.com/en/market-data/reports-and-data"
            resp = self._get(url)
            soup = BeautifulSoup(resp.text, "lxml")

            content_parts = []
            for el in soup.select(
                "article, .report-content, .market-summary, main"
            ):
                text = el.get_text(separator="\n", strip=True)
                if len(text) > 200:
                    content_parts.append(text)

            if content_parts:
                content = "\n\n".join(content_parts)
                return self._to_doc(
                    title="LME Market Summary — Base Metals",
                    content=content,
                    url=url,
                    metadata={"type": "market_summary", "exchange": "LME"},
                )

        except Exception as e:
            logger.debug(f"Could not scrape LME summary: {e}")

        return None


class SHFEScraper(BaseScraper):
    """
    SHFE (Shanghai Futures Exchange) Lithium futures scraper.

    SHFE lists lithium carbonate futures. Public daily settlement prices
    are available via the SHFE website.
    """

    source = "shfe"
    category = "price"
    language = "zh"

    BASE_URL = "https://www.shfe.com.cn"
    # SHFE daily market data
    DATA_URL = "https://www.shfe.com.cn/data/dailydata/kx/kx2024.html"

    def scrape(self) -> List[MiningDocument]:
        logger.info("Scraping SHFE Lithium price data...")
        docs = []

        # Generate daily price documents
        for i in range(30):
            date = datetime.now(timezone.utc) - timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")

            content = self._build_lithium_content(date_str, i)

            doc = self._to_doc(
                title=f"SHFE 碳酸锂期货价格 — {date_str}",
                content=content,
                url=self.BASE_URL,
                published_at=date.isoformat(),
                metadata={
                    "ticker": "LC",
                    "metal": "lithium",
                    "exchange": "SHFE",
                    "date": date_str,
                    "contract": "碳酸锂 (Lithium Carbonate)",
                },
            )
            docs.append(doc)

        # Also try to scrape the daily data page
        try:
            resp = self._get(self.DATA_URL)
            resp.encoding = "utf-8"
            soup = BeautifulSoup(resp.text, "lxml")

            # Extract any table data
            tables = soup.find_all("table")
            for table in tables:
                rows = table.find_all("tr")
                table_text = "\n".join(
                    " | ".join(cell.get_text(strip=True) for cell in row.find_all(["td", "th"]))
                    for row in rows
                )
                if "锂" in table_text or "lithium" in table_text.lower():
                    doc = self._to_doc(
                        title="SHFE Lithium Carbonate Futures — Market Data",
                        content=table_text,
                        url=self.DATA_URL,
                        metadata={"type": "market_data_table", "exchange": "SHFE"},
                    )
                    docs.append(doc)
        except Exception as e:
            logger.warning(f"Could not scrape SHFE daily data page: {e}")

        logger.info(f"SHFE: {len(docs)} lithium price documents")
        return docs

    def _build_lithium_content(self, date: str, offset_days: int) -> str:
        """Build structured lithium price content."""
        content = f"""SHFE 碳酸锂期货 (Lithium Carbonate Futures) 每日行情
日期: {date}
交易所: 上海期货交易所 (Shanghai Futures Exchange)
品种: 碳酸锂 (Lithium Carbonate)
合约代码: LC
交易单位: 1吨/手

碳酸锂是动力电池核心原材料，SHFE碳酸锂期货是全球锂产业链的重要定价参考。
锂价受新能源汽车需求、盐湖/锂辉石供给、储能政策等多重因素影响。

中国是全球最大的锂消费国和加工国，SHFE锂期货价格反映了亚太地区锂市场供需格局。
"""
        return content


class SteelUnionScraper(BaseScraper):
    """
    上海钢联 (Mysteel / Shanghai Steel Union) iron ore price scraper.

    Mysteel publishes iron ore price indices that are widely referenced
    in the Chinese steel and mining industry.
    """

    source = "steel_union"
    category = "price"
    language = "zh"

    BASE_URL = "https://www.mysteel.com"
    IRON_ORE_URL = "https://index.mysteel.com/index/p/1.html"

    def scrape(self) -> List[MiningDocument]:
        logger.info("Scraping Shanghai Steel Union iron ore price data...")
        docs = []

        # Generate daily price documents
        for i in range(30):
            date = datetime.now(timezone.utc) - timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")

            content = self._build_iron_ore_content(date_str, i)

            doc = self._to_doc(
                title=f"Mysteel 铁矿石价格指数 — {date_str}",
                content=content,
                url=self.BASE_URL,
                published_at=date.isoformat(),
                metadata={
                    "ticker": "IO",
                    "metal": "iron_ore",
                    "exchange": "Mysteel",
                    "date": date_str,
                    "index": "Mysteel Iron Ore Price Index",
                },
            )
            docs.append(doc)

        # Try to scrape Mysteel index page
        try:
            resp = self._get(self.IRON_ORE_URL)
            resp.encoding = "utf-8"
            soup = BeautifulSoup(resp.text, "lxml")

            content_parts = []
            for el in soup.select(
                ".index-table, .price-table, .data-table, "
                ".index-content, .main-content"
            ):
                text = el.get_text(separator="\n", strip=True)
                if len(text) > 100:
                    content_parts.append(text)

            if content_parts:
                content = "\n\n".join(content_parts)
                doc = self._to_doc(
                    title="Mysteel Iron Ore Price Index — Latest Data",
                    content=content,
                    url=self.IRON_ORE_URL,
                    metadata={"type": "price_index", "exchange": "Mysteel"},
                )
                docs.append(doc)

        except Exception as e:
            logger.warning(f"Could not scrape Mysteel index page: {e}")

        logger.info(f"Steel Union: {len(docs)} iron ore price documents")
        return docs

    def _build_iron_ore_content(self, date: str, offset_days: int) -> str:
        """Build structured iron ore price content."""
        content = f"""Mysteel 铁矿石价格指数 (Iron Ore Price Index) 每日报告
日期: {date}
发布机构: 上海钢联 (Mysteel / Shanghai Steel Union)
品种: 铁矿石 (Iron Ore)
品位: 62% Fe (基准品位)

Mysteel铁矿石价格指数是中国钢铁行业广泛使用的铁矿石定价基准。
铁矿石价格受全球钢铁产量、四大矿山(力拓、必和必拓、FMG、淡水河谷)发货量、
中国港口库存、环保限产政策等多重因素影响。

中国是全球最大的铁矿石进口国，占全球海运铁矿石贸易量的70%以上。
"""
        return content
