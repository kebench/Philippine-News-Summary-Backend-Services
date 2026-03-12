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

### Prerequisites
- Docker
- AWS CLI configured with `ph-news-deploy-policy` permissions
- ECR repository created (`ph-news-ingestion`)

### Build and Push to ECR

Authenticate Docker to ECR:
```bash
aws ecr get-login-password --region eu-west-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.eu-west-1.amazonaws.com
```

Build and push:
```bash
docker build -f services/ingestion/Dockerfile . -t ph-news-ingestion
docker tag ph-news-ingestion:latest <account-id>.dkr.ecr.eu-west-1.amazonaws.com/ph-news-ingestion:latest
docker push <account-id>.dkr.ecr.eu-west-1.amazonaws.com/ph-news-ingestion:latest
```

### Lambda Configuration
- Runtime: Container image
- Memory: at least 2048MB
- Timeout: 5 minutes
- Environment variables: `MONGODB_URI`, `LOG_LEVEL`, `MONGO_DB_NAME=ph_news`

## Local Testing

### Prerequisites
Download the AWS Lambda Runtime Interface Emulator (RIE) once to the project root:

**Windows (PowerShell):**
```powershell
curl -Lo aws-lambda-rie.exe https://github.com/aws/aws-lambda-runtime-interface-emulator/releases/latest/download/aws-lambda-rie-x86_64
```

**Mac/Linux:**
```bash
curl -Lo aws-lambda-rie https://github.com/aws/aws-lambda-runtime-interface-emulator/releases/latest/download/aws-lambda-rie
chmod +x aws-lambda-rie
```

> Note: `aws-lambda-rie` and `aws-lambda-rie.exe` are already in `.gitignore`

### Run Locally

**Windows (PowerShell):**
```powershell
docker run --env-file services/ingestion/.env -p 9000:8080 `
  -v ${PWD}/aws-lambda-rie.exe:/aws-lambda-rie `
  --entrypoint /aws-lambda-rie `
  ph-news-ingestion /usr/local/bin/python -m awslambdaric handler.handler
```

**Mac/Linux:**
```bash
docker run --env-file services/ingestion/.env -p 9000:8080 \
  -v $(pwd)/aws-lambda-rie:/aws-lambda-rie \
  --entrypoint /aws-lambda-rie \
  ph-news-ingestion /usr/local/bin/python -m awslambdaric handler.handler
```

### Invoke the Handler
In a second terminal:

**Windows (PowerShell):**
```powershell
curl -X POST "http://localhost:9000/2015-03-31/functions/function/invocations" `
  -H "Content-Type: application/json" `
  -d '{}'
```

**Mac/Linux:**
```bash
curl -X POST "http://localhost:9000/2015-03-31/functions/function/invocations" \
  -H "Content-Type: application/json" \
  -d '{}'
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