# ph-news-ingestion — Pipeline Document

**Version:** 0.1.1  
**Date:** 2026-03-23  
**Author:** Kevin  
**Status:** Live

---

## 1. Overview

The ingestion pipeline is the foundational component of `ph-news-backend`. It is responsible for crawling Philippine news sources daily, extracting headlines, and storing them in MongoDB. It supports three source types: web crawling (Playwright + BeautifulSoup), RSS feeds (feedparser), and REST APIs.

---

## 2. Goals

- Ingest headlines daily from multiple Philippine news sources
- Deduplicate headlines across runs via `headline_hash`
- Store raw headlines in MongoDB for downstream processing (summarizer, classifier, etc.)
- Remain config-driven — adding a new source requires only a `sources.yaml` entry, no code changes

---

## 3. Functional Requirements

| ID | Requirement |
|----|-------------|
| FR-01 | Crawl headlines from sources defined in `sources.yaml` |
| FR-02 | Support three source types: web crawler, RSS feed, API |
| FR-03 | Extract headline text and article URL per item |
| FR-04 | Deduplicate headlines using a hash of the article URL |
| FR-05 | Bulk upsert headlines into MongoDB `RawHeadline` collection |
| FR-06 | Tag each headline with `crawled_at` (datetime) and `crawled_date` (date) |
| FR-07 | Invoke the Summarizer Starter Lambda asynchronously after ingestion completes |
| FR-08 | Run on a daily schedule aligned to Philippine Standard Time (PST, UTC+8) |

---

## 4. Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| NFR-01 | Must run within AWS Lambda (15-minute max timeout) |
| NFR-02 | Observed runtime: 40–90 seconds per run |
| NFR-03 | Containerized via Docker, deployed to ECR (~1GB image) |
| NFR-04 | Config-driven design via `sources.yaml` — no hardcoded source logic |
| NFR-05 | Generic CSS selectors — no hardcoded tag assumptions (e.g. no assumed `h3`) |
| NFR-06 | Shared logger used consistently across all modules |
| NFR-07 | Code must be well-commented — no exceptions |

---

## 5. Tech Stack

| Component | Choice |
|-----------|--------|
| Language | Python 3.11 |
| Web crawling | Playwright + BeautifulSoup |
| RSS ingestion | feedparser |
| API ingestion | httpx |
| ODM | Beanie (MongoDB) |
| Storage | PyMongo bulk upserts via `get_pymongo_collection()` |
| Container base | `python:3.11-slim-bookworm` |
| Lambda runtime | `awslambdaric` |
| Local testing | AWS Lambda RIE (mounted as volume, not baked into image) |
| Scheduling | AWS EventBridge |
| Registry | AWS ECR (eu-west-1) |

---

## 6. System Architecture

### 6.1 High-Level Flow

```
EventBridge (daily schedule — PST-aligned)
    └─► Ingestion Lambda (Docker on ECR)
            ├─► sources.yaml
            │       ├─► crawler/generic.py     (Playwright + BeautifulSoup)
            │       ├─► rss/generic.py          (feedparser)
            │       └─► api_caller/generic.py   (httpx)
            ├─► Bulk upsert → MongoDB (RawHeadline collection)
            └─► boto3.invoke (async) → Summarizer Starter Lambda
```

### 6.2 Playwright Flags (Lambda-compatible Chromium)

```
--no-sandbox
--disable-setuid-sandbox
--disable-dev-shm-usage
--disable-gpu
--single-process
```

### 6.3 Local Testing

RIE (Runtime Interface Emulator) is mounted as a Docker volume at test time — it is not baked into the image. This keeps the production image clean and environment-appropriate.

---

## 7. Data Model — `RawHeadline`

| Field | Type | Notes |
|-------|------|-------|
| `article_url` | str | Source URL, used as dedup key |
| `headline_hash` | str | SHA hash of `article_url` |
| `headline` | str | Extracted headline text |
| `source` | str | Publication name (from `sources.yaml`) |
| `crawled_at` | datetime | UTC timestamp of crawl |
| `crawled_date` | date | Date portion of `crawled_at` (for daily scoping) |

---

## 8. File Structure

```
ingestion/
├── crawler/
│   ├── __init__.py
│   └── generic.py       # Playwright + BeautifulSoup crawler
├── rss/
│   ├── __init__.py
│   └── generic.py       # feedparser RSS ingestion
├── api_caller/
│   ├── __init__.py
│   └── generic.py       # httpx API caller
├── models.py            # RawHeadline Beanie model
├── handler.py           # Lambda entry point
└── sources.yaml         # Config-driven source definitions
```

---

## 9. Source Configuration (`sources.yaml`)

Each source entry defines its type and all parameters needed for ingestion. Scroll behaviour, selectors, and field mappings are configured per source — not hardcoded.

```yaml
sources:
  - name: Inquirer
    type: crawler
    url: https://www.inquirer.net
    selectors:
      headline: "a.article-title"
    scroll: true
    scroll_count: 3

  - name: Rappler RSS
    type: rss
    url: https://www.rappler.com/feed

  - name: NewsAPI PH
    type: api
    url: https://newsapi.org/v2/top-headlines
    params:
      country: ph
    field_map:
      headline: title
      article_url: url
```

---

## 10. Versioning

| Version | Description |
|---------|-------------|
| v0.1.0 | Ingestion pipeline — crawler, RSS, API, MongoDB upsert |
| v0.1.1 | Lambda deployment fixes — ECR, EventBridge, IAM |

---

## 11. Cost Estimates (eu-west-1)

| Service | Usage | Est. Monthly Cost |
|---------|-------|-------------------|
| ECR | ~1GB image storage | ~$0.10 |
| Lambda | 1 run/day × ~65s avg × 1GB memory ≈ 1,950 GB-seconds (within free tier) | ~$0.00 |
| CloudWatch Logs | ~1MB/month (within 5GB free tier), 90-day retention policy | ~$0.00 |
| EventBridge | 1 rule, 30 invocations/month (within free tier) | ~$0.00 |
| **Total** | | **~$0.10/month** |

---

## 12. IAM

A least-privilege IAM user is provisioned scoped to `ph-news-*` resources in `eu-west-1`. Permissions cover ECR push/pull, Lambda deployment, and EventBridge rule management only.

---

## 13. Out of Scope

- Full article content fetching
- Headline classification or enrichment
- Real-time or streaming ingestion
- Frontend display
