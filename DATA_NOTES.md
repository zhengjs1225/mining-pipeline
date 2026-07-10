# DATA NOTES — Mining Intelligence Pipeline

## Overview

三源聚合管线：矿业新闻 + 关键矿产政策 + 价格数据，入向量库供自然语言查询。

## Data Sources

| # | Source | URL | Category | Language | Method |
|---|--------|-----|----------|----------|--------|
| 1 | Mining.com | https://www.mining.com/feed/ | news | en | RSS + full-text extraction |
| 2 | S&P Global Mining | RSS feed | news | en | RSS + full-text extraction |
| 3 | 中国稀土集团 | https://www.creg.com.cn | policy | zh | HTML scraping (listing + article pages) |
| 4 | Australia DISR | https://www.industry.gov.au | policy | en | HTML scraping (strategy page + publications listing) |
| 5 | LME | https://www.lme.com | price | en | HTML scraping + structured daily price docs |
| 6 | SHFE (碳酸锂) | https://www.shfe.com.cn | price | zh | HTML scraping + structured daily price docs |
| 7 | 上海钢联 (Mysteel) | https://www.mysteel.com | price | zh | HTML scraping + structured daily price docs |

### Volume Requirements
- **Per source**: ≥200 articles/records (≥600 total)
- **Time range**: ≥30 days
- **Total corpus target**: 1,400+ documents

---

## Unified Schema

### `MiningDocument`

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `id` | `str` | **Primary key** — SHA256(source + url) | `"a1b2c3d4..."` |
| `source` | `str` | Source identifier | `"mining_com"`, `"lme"`, `"rare_earth_cn"` |
| `category` | `str` | Data category | `"news"`, `"policy"`, `"price"` |
| `title` | `str` | Document title | `"LME Copper Price — 2025-06-01"` |
| `content` | `str` | Full text or structured summary | (full article text / price report) |
| `url` | `str` | Source URL | `"https://www.mining.com/..."` |
| `published_at` | `str?` | ISO 8601 publication date | `"2025-06-01T00:00:00+00:00"` |
| `language` | `str` | Language code | `"zh"` or `"en"` |
| `metadata` | `dict` | Source-specific extras | `{"minerals_mentioned": ["锂", "钴"]}` |
| `ingested_at` | `str?` | ISO 8601 ingestion timestamp | `"2025-06-15T10:30:00+00:00"` |

### Metadata Sub-schema (by category)

#### News (`category: "news"`)
```json
{
  "rss_summary": "Original RSS summary (first 500 chars)"
}
```

#### Policy (`category: "policy"`)
```json
{
  "minerals_mentioned": ["锂", "稀土", "cobalt"],
  "policy_types": ["export_quota", "environmental", "investment"]
}
```

Policy types enum:
- `export_quota` — 出口配额 / 出口管制
- `production_cap` — 产量上限 / 生产指标
- `environmental` — 环保 / ESG
- `subsidy` — 补贴 / 扶持
- `strategic_reserve` — 战略储备
- `trade_restriction` — 关税 / 限制 / 禁令
- `investment` — 投资 / 资金支持
- `processing` — 下游加工 / 精炼
- `supply_chain` — 供应链多元化
- `indigenous` — 原住民权益 (AU-specific)

#### Price (`category: "price"`)
```json
{
  "ticker": "CA",
  "metal": "copper",
  "exchange": "LME",
  "date": "2025-06-01",
  "price_data": {
    "current_price": 8520.50,
    "volume": 12500,
    "open_interest": 280000
  }
}
```

---

## Primary Key & Deduplication Strategy

### Primary Key
```
id = SHA256(source + ":" + url)
```
Deterministic, collision-resistant. Same article from same URL always gets the same ID.

### Dedup Pipeline (3-stage)

| Stage | Method | What it catches |
|-------|--------|-----------------|
| **1. Exact ID** | `SHA256(source + url)` | Same URL re-scraped |
| **2. Content Fingerprint** | `MD5(normalize(content[:2000]))` | Same article at different URLs (syndication) |
| **3. Near-Duplicate** | Jaccard similarity on bigrams (threshold: 0.85) | Slightly edited re-posts |

#### Stage 3 Details
- **Chinese text**: character bigrams (字级别二元组)
- **English text**: word bigrams (after filtering stop words <3 chars)
- **Threshold**: Jaccard ≥ 0.85 → considered duplicate
- **Keep policy**: first occurrence kept, subsequent ones dropped

---

## Text Cleaning Pipeline

1. HTML tag removal (`<[^>]+>`)
2. URL removal (keep surrounding text)
3. Social media / sharing boilerplate removal
4. Cookie / privacy banner text removal
5. Chinese full-width space normalization (`　` → ` `)
6. Whitespace collapse (multiple spaces/newlines)
7. Chinese website boilerplate removal (版权/ICP备案/etc.)
8. Minimum content length check:
   - zh: ≥30 characters
   - en: ≥50 characters
9. JavaScript-disabled warning detection

---

## Embedding Configuration

| Parameter | Value |
|-----------|-------|
| Model | `BAAI/bge-m3` |
| Dimension | 1024 |
| Max tokens | 8192 |
| Normalization | L2 (cosine similarity) |
| Languages | Chinese + English + multilingual |
| Embedding text format | `[{source}] [{category}] {title}\n{content[:2000]}` |

---

## Vector Store (ChromaDB)

| Parameter | Value |
|-----------|-------|
| Collection name | `mining_docs` |
| Distance metric | Cosine |
| Index type | HNSW |
| Storage | Persistent (`data/chroma/`) |

### ChromaDB Metadata Fields (for filtering)
- `source` — filter by source
- `category` — filter by category (news/policy/price)
- `title` — document title
- `url` — source URL
- `language` — zh/en
- `published_at` — publication date
- `minerals` — JSON array of mentioned minerals
- `policy_types` — JSON array of policy types
- `ingested_at` — ingestion timestamp

---

## API Interface

### `POST /query`
```json
{
  "question": "近7天澳洲锂出口政策有何变化?",
  "top_k": 5,
  "generate_answer": true,
  "source_filter": null,
  "category_filter": "policy",
  "days_filter": 7
}
```

Response:
```json
{
  "question": "...",
  "answer": "Generated LLM answer based on retrieved documents...",
  "retrieved_docs": [
    {
      "id": "abc123",
      "title": "Australia Updates Critical Minerals Strategy",
      "source": "disr_au",
      "category": "policy",
      "url": "https://...",
      "published_at": "2025-06-01T00:00:00+00:00",
      "content_preview": "The Australian Government has announced...",
      "relevance_score": 0.9234
    }
  ],
  "total_in_store": 1420,
  "query_time_ms": 245.3
}
```

---

## Evaluation Metrics

### recall@5
- 20 ground-truth Q&A pairs (7 policy, 7 news, 6 price)
- Bilingual: 10 zh + 10 en
- A "hit" requires: (1) retrieved doc from a relevant source AND (2) content matches ≥1 expected keyword
- Per-category and per-language breakdowns

### Answer Faithfulness
- Generates LLM answer from retrieved context
- Checks what fraction of answer statements are supported by context
- Proxy metric: keyword-overlap between answer sentences and context
- Full metric: LLM judge ("Is this answer fully supported by context?")

---

## Running the Pipeline

```bash
# Install dependencies
pip install -r requirements.txt

# Run full ingestion
python -m pipeline.ingest

# Single source
python -m pipeline.ingest --source mining_com

# Dry run (no DB write)
python -m pipeline.ingest --dry-run

# Start API server
python -m serve.app
# or: uvicorn serve.app:app --host 0.0.0.0 --port 8000

# Run evaluation
python -m eval.evaluate --k 5 --verbose

# With faithfulness
python -m eval.evaluate --faithfulness --output eval_results.json
```

---

## Known Limitations & Mitigations

| Issue | Mitigation |
|-------|------------|
| LME real-time data requires login | Use delayed public data + structured daily summaries |
| S&P Global paywall on full articles | Use RSS summaries as fallback content |
| 中国稀土集团 anti-scraping | UA rotation, rate limiting, exponential backoff |
| Mysteel pricing behind login | Public index pages + structured summaries |
| DISR PDF publications not text-extractable | Link to HTML versions; fallback to page summaries |
| No real LLM API key configured | Set `LLM_API_KEY` + `LLM_BASE_URL` env vars; keyword-based answer generation as fallback |

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `EMBEDDING_MODEL` | `BAAI/bge-m3` | Sentence-transformer model |
| `LLM_BASE_URL` | `https://api.openai.com/v1` | LLM API base URL |
| `LLM_API_KEY` | (empty) | LLM API key |
| `LLM_MODEL` | `gpt-4o-mini` | LLM model name |
| `SCRAPE_DAYS` | `30` | Days of history to scrape |
| `MIN_ARTICLES_PER_SOURCE` | `200` | Minimum articles per source |
