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
| `ingestion` | Crawls PH news sources + calls external APIs | EventBridge cron |
| `summarization` | LLM summarization via SageMaker | EventBridge cron (daily) |
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
cp services/ingestion/.env.example services/ingestion/.env
# Fill in your values
```

Set up the virtual environment:

```bash
cd services/ingestion
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Mac/Linux** — use the Makefile from the project root:

```bash
make run
```

**Windows** — set `PYTHONPATH` manually in PowerShell:

```powershell
$env:PYTHONPATH="..\..\packages"
python handler.py
```

Or with a `.bat` file:

```bat
set PYTHONPATH=..\..\packages
python handler.py
```

## Deployment

Each service deploys as a Docker container on Lambda. Build from the project root:

```bash
docker build -f services/ingestion/Dockerfile . -t ph-news-ingestion
docker run --env-file services/ingestion/.env -p 9000:8080 ph-news-ingestion
```

Invoke
```bash
curl -X POST "http://localhost:9000/2015-03-31/functions/function/invocations" -d '{}'
```

## Project Structure

```
ph-news-backend/
├── packages/
│   └── shared/             # Beanie models, DB client, utils
├── services/
│   ├── ingestion/          # Crawler + API caller
│   ├── summarization/      # LLM summarization via SageMaker
│   └── api/                # FastAPI read API
├── infra/                  # EventBridge + SageMaker configs
└── Makefile
```