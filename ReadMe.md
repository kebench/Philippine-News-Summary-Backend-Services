# ph-news-backend

Backend services for the Philippine Daily News Summarizer.

## Architecture

```
EventBridge (cron)
    │
    ▼
services/ingestion      →  MongoDB (raw_headlines)
    │
    ▼ (daily trigger)
services/summarization  →  MongoDB (processed_summaries)
    │
    ▼
services/api            →  Frontend
```

## Services

| Service | Description | Trigger |
|---|---|---|
| `ingestion` | Crawls PH news sources + calls News API | EventBridge cron |
| `summarization` | Runs LLM summarization via SageMaker | EventBridge cron (daily) |
| `api` | FastAPI read API for the frontend | API Gateway (Lambda) |

## Shared Package

`packages/shared` contains Beanie document models, MongoDB client, and utilities shared across all services.

## Getting Started

### Prerequisites
- Python 3.11+
- Docker
- MongoDB Atlas account (free tier)
- AWS account

### Local Development

```bash
cd services/ingestion # Or whatever service that you want to work on
cp .env.example .env
# Fill in your values

python -m venv .venv # If no venv
source .venv/bin/activate
# Windows (PowerShell): .venv\Scripts\Activate.ps1
```

### Running a service locally

```bash
pip install -r requirements.txt
python handler.py
```

## Deployment

Each service deploys independently as a Lambda function (ingestion, summarization, api). See `infra/` for EventBridge rules and SageMaker config.

## Project Structure

```
ph-news-backend/
├── packages/
│   └── shared/             # Beanie models, DB client, utils
├── services/
│   ├── ingestion/          # Crawler + API caller
│   ├── summarization/      # LLM summarization via SageMaker
│   └── api/                # FastAPI read API
└── infra/                  # EventBridge + SageMaker configs
```