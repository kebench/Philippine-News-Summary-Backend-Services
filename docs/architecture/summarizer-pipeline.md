# ph-news-summarizer — Project Plan

**Version:** 0.1.0-draft  
**Date:** 2026-03-23  
**Author:** Kevin  
**Status:** Planning

---

## 1. Overview

`ph-news-summarizer` is a component of the `ph-news-backend` monorepo responsible for generating structured headline digests from raw ingested news headlines. It groups semantically similar headlines into topic clusters and produces a short narrative summary per cluster, mimicking a news briefing format.

This component also serves as the primary vehicle for learning the full Machine Learning Engineering (MLE) lifecycle — from local model inference and fine-tuning to cloud deployment on AWS.

---

## 2. Goals

### 2.1 Product Goals
- Generate a daily headline digest grouped by topic from raw Philippine news headlines
- Store digests in MongoDB for downstream consumption (e.g. frontend, notifications)
- Integrate cleanly into the existing `ph-news-backend` ingestion pipeline

### 2.2 Learning Goals
- Understand model serving and inference (vLLM, FastAPI)
- Understand fine-tuning with LoRA/QLoRA (Unsloth)
- Understand the full model deployment lifecycle: local → EC2 → SageMaker
- Understand dataset preparation and evaluation for NLP tasks

---

## 3. Functional Requirements

| ID | Requirement |
|----|-------------|
| FR-01 | Accept a batch of raw headlines (title + source + date) as input |
| FR-02 | Group semantically related headlines into topic clusters |
| FR-03 | Generate a 1–2 sentence narrative digest per cluster |
| FR-04 | Assign a human-readable topic label per cluster (e.g. "Fuel Price Crisis") |
| FR-05 | Store each cluster as a `HeadlineDigest` document in MongoDB |
| FR-06 | Track which `RawHeadline` documents contributed to each digest via `headline_hashes` |
| FR-07 | Be invocable as an AWS Lambda function |
| FR-08 | Be triggerable asynchronously from the ingestion Lambda via `boto3` |
| FR-09 | Scope digest generation to a specific `crawled_date` (no cross-day bleed) |

---

## 4. Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| NFR-01 | Model must run on 16GB VRAM locally (NVIDIA RTX 5070 Ti) |
| NFR-02 | Inference latency must be acceptable for async Lambda invocation (no hard SLA) |
| NFR-03 | All components must be containerized via Docker |
| NFR-04 | Architecture must follow `ph-news-backend` conventions: config-driven, separation of concerns, shared logger |
| NFR-05 | CUDA 12.8+ and PyTorch 2.6+ required (Blackwell GPU compatibility) |
| NFR-06 | Code must be well-commented — no exceptions |

---

## 5. Tech Stack

### 5.1 Model
| Component | Choice | Rationale |
|-----------|--------|-----------|
| Base model | Llama 3.1 8B or Mistral 7B | Strong instruction following, fits in 16GB VRAM at fp16 |
| Precision | fp16 (local), quantized for EC2 if needed | Full quality locally, cost-optimised on cloud |
| Fine-tuning method | LoRA / QLoRA | Parameter-efficient, consumer GPU friendly |

### 5.2 Infrastructure & Tooling
| Component | Choice |
|-----------|--------|
| Inference server | vLLM |
| Fine-tuning framework | Unsloth |
| API wrapper | FastAPI |
| Containerization | Docker |
| Local GPU runtime | CUDA 12.8+, PyTorch 2.6+ |
| Cloud inference (Phase 3) | AWS EC2 (GPU instance, e.g. `g4dn.xlarge`) |
| Managed inference (Phase 4) | AWS SageMaker |
| Orchestration | AWS Lambda (caller), EventBridge (schedule) |
| Database | MongoDB via Beanie ODM |
| Language | Python 3.11 |

---

## 6. System Architecture

### 6.1 Design Approach

The summarizer is built as a **microservices pipeline**. Each Lambda has a single responsibility, making it straightforward to identify which service failed when something goes wrong. The EC2 inference instance is **not always-on** — it is started on demand and stopped after use to avoid unnecessary cost.

### 6.2 High-Level Flow

```
EventBridge (daily schedule)
    └─► Ingestion Lambda
            ├─► Crawls headlines → stores RawHeadline in MongoDB
            └─► boto3.invoke (async)
                    └─► Starter Lambda
                            ├─► Starts EC2 inference instance
                            └─► Exits immediately

                                    EC2 (boots + loads model)
                                        └─► Publishes "ready" event to SNS

                                                └─► SNS triggers Summarizer Lambda
                                                        ├─► Queries MongoDB for today's RawHeadlines
                                                        ├─► POST headlines to EC2 inference (private IP)
                                                        │       └─► vLLM + FastAPI returns clustered digest (JSON)
                                                        ├─► Upserts HeadlineDigest docs to MongoDB
                                                        └─► Stops EC2 instance

EventBridge (watchdog rule)
    └─► Watchdog Lambda
            └─► Force-stops EC2 if running longer than X minutes (safety net)
```

### 6.3 Service Responsibilities

| Service | Responsibility | Failure = |
|---------|---------------|-----------|
| Starter Lambda | Start EC2 instance, exit | EC2 never starts |
| EC2 boot script | Load model, publish SNS ready event | Summarizer never triggered |
| Summarizer Lambda | Fetch headlines, call inference, store digests, stop EC2 | Digests not generated, EC2 may stay on |
| Watchdog Lambda | Force-stop EC2 if runtime exceeds threshold | EC2 left running (cost risk) |

### 6.4 VPC Design

The EC2 inference instance is placed in a **public subnet** but is locked down via a strict **security group** that allows inbound traffic only from the Summarizer Lambda. No NAT Gateway is used — this keeps the architecture within the €10/month budget. A private subnet with NAT Gateway can be revisited if this project moves toward production.

```
ph-news-summarizer VPC
└── Public Subnet
        ├── EC2 inference instance
        │       Security Group: inbound port 8000 from Summarizer Lambda SG only
        │                        inbound port 22 from developer IP only
        │                        outbound all (model downloads, SNS publish, MongoDB Atlas)
        └── Summarizer Lambda (VPC-attached)
                ├─► EC2 via public IP on port 8000 (inference calls)
                └─► MongoDB Atlas over internet (outbound)
```

A dedicated VPC isolates all summarizer infrastructure cleanly from the rest of `ph-news-backend`. If the summarizer stack is torn down or redesigned, it does not affect existing ingestion infrastructure.

### 6.5 Data Flow

```
RawHeadline (MongoDB)
    │  title, article_url, headline_hash, crawled_date, source
    ▼
Summarizer Lambda
    │  batches headlines by crawled_date
    ▼
EC2 Inference (vLLM + FastAPI) — public subnet, SG-restricted
    │  input:  list of {index, title, source}
    │  output: list of {topic, digest, headline_indices}
    ▼
HeadlineDigest (MongoDB)
    topic, digest, headline_hashes, headline_count, digest_date, created_at
```

---

## 7. Data Models

### 7.1 Input — `RawHeadline` (existing)

| Field | Type |
|-------|------|
| `article_url` | str |
| `headline_hash` | str |
| `headline` | str |
| `source` | str |
| `crawled_at` | datetime |
| `crawled_date` | date |

### 7.2 Output — `HeadlineDigest` (new)

| Field | Type | Notes |
|-------|------|-------|
| `digest_date` | date | The `crawled_date` of the source headlines |
| `topic` | str | Model-inferred label, e.g. "Fuel Price Crisis" |
| `digest` | str | 1–2 sentence narrative summary |
| `headline_hashes` | list[str] | Refs to contributing `RawHeadline` docs |
| `headline_count` | int | Number of headlines in cluster |
| `created_at` | datetime | |

---

## 8. Proposed File Structure

```
summarizer/
├── starter/
│   ├── __init__.py
│   └── handler.py       # Starter Lambda — starts EC2, exits
├── summarizer/
│   ├── __init__.py
│   ├── handler.py       # Summarizer Lambda — fetch headlines, call inference, store, stop EC2
│   ├── prompt.py        # Prompt construction + inference API call
│   └── models.py        # HeadlineDigest Beanie model
├── watchdog/
│   ├── __init__.py
│   └── handler.py       # Watchdog Lambda — force-stop EC2 if running too long
└── ec2/
    └── boot.sh          # EC2 user data script — loads model, publishes SNS ready event
```

Each Lambda is independently deployable. The `ec2/` directory holds the boot script baked into the EC2 instance or passed as user data.

---

## 9. Prompt Design (Draft)

The model receives a structured list of headlines and is instructed to return JSON:

**Input format:**
```
1. [Inquirer] Oil prices break through ₱100/L mark
2. [Rappler] Fuel hike expected to push transport fare increase
3. [GMA] DOE orders review of oil company pricing
4. [Inquirer] Marcos signs new infrastructure bill
5. [PhilStar] DPWH to begin Metro Manila road expansion
```

**Expected output format (JSON):**
```json
[
  {
    "topic": "Fuel Price Crisis",
    "digest": "Oil prices have surpassed the ₱100/L threshold, prompting government scrutiny and anticipating ripple effects on transport fares.",
    "headline_indices": [1, 2, 3]
  },
  {
    "topic": "Infrastructure Push",
    "digest": "The Marcos administration has signed a new infrastructure bill, with the DPWH set to begin road expansion projects in Metro Manila.",
    "headline_indices": [4, 5]
  }
]
```

---

## 10. Development Phases

### Phase 1 — Local Inference (v0.1.0)
- [ ] Set up vLLM locally with Llama 3.1 8B or Mistral 7B
- [ ] Wrap with a FastAPI `/summarize` endpoint
- [ ] Validate CUDA 12.8 + PyTorch 2.6 compatibility on RTX 5070 Ti
- [ ] Build `prompt.py` — prompt construction and API call logic
- [ ] Build `handler.py` — Lambda orchestration logic (runnable locally)
- [ ] Build `models.py` — `HeadlineDigest` Beanie model
- [ ] End-to-end local test with real `RawHeadline` data from MongoDB

### Phase 2 — Fine-tuning (v0.2.0)
- [ ] Prepare headline digest dataset (curated PH news examples)
- [ ] Fine-tune base model with LoRA/QLoRA via Unsloth
- [ ] Evaluate output quality vs. base model
- [ ] Version the fine-tuned model (weights + adapter)

### Phase 3 — EC2 Deployment (v0.3.0)
- [ ] Provision dedicated VPC with public subnet
- [ ] Provision GPU EC2 instance (e.g. `g4dn.xlarge`) with 40GB gp3 EBS volume
- [ ] Configure security group — inbound port 8000 from Summarizer Lambda SG only, port 22 from developer IP only
- [ ] Write `ec2/boot.sh` — loads model via vLLM, publishes SNS ready event
- [ ] Containerize vLLM + FastAPI inference service
- [ ] Deploy and validate Starter Lambda
- [ ] Deploy and validate Summarizer Lambda (VPC-attached)
- [ ] Deploy and validate Watchdog Lambda + EventBridge rule
- [ ] Configure SNS topic — EC2 publishes, Summarizer Lambda subscribes
- [ ] End-to-end pipeline test on AWS

### Phase 4 — SageMaker (v0.4.0)
- [ ] Re-deploy model as a SageMaker real-time endpoint
- [ ] Evaluate whether Starter/Watchdog Lambdas are still needed (SageMaker manages scaling)
- [ ] Update Summarizer Lambda to call SageMaker endpoint instead of EC2 private IP
- [ ] Document cost and operational comparison: EC2 vs SageMaker

---

## 11. Integration with ph-news-backend

The Ingestion Lambda invokes the **Starter Lambda** asynchronously at the end of its run, passing the `crawled_date` so the Summarizer Lambda knows which day's headlines to process:

```python
# In ingestion handler.py — after bulk upsert completes
lambda_client.invoke(
    FunctionName="ph-news-summarizer-starter",
    InvocationType="Event",  # async, fire-and-forget
    Payload=json.dumps({"crawled_date": str(crawled_date)})
)
```

The `crawled_date` is passed through the chain: Starter Lambda embeds it in the EC2 instance tag or SNS message, so the Summarizer Lambda receives it when triggered by SNS.

---

## 12. Open Questions

| # | Question | Notes |
|---|----------|-------|
| OQ-01 | What EC2 instance type to use in Phase 3? | `g4dn.xlarge` (T4, 16GB) is cheapest GPU option |
| OQ-02 | Fine-tuning dataset source? | Manual curation vs. synthetic generation |
| OQ-03 | How to handle days with very few headlines (<5)? | Skip digest, or generate anyway? |
| OQ-04 | Should digest generation be idempotent? | i.e. re-running same date should upsert, not duplicate |
| OQ-05 | Watchdog threshold — how long before force-stop? | Depends on measured EC2 boot + inference time |
| OQ-06 | How is `crawled_date` passed from EC2 to Summarizer Lambda via SNS? | Embed in SNS message payload vs. EC2 instance tag |

---

## 13. Cost Estimates (eu-west-1)

Budget ceiling: **€10/month**. All figures are approximate and based on a daily run schedule.

### Ingestion Pipeline (existing)

| Service | Usage | Est. Monthly Cost |
|---------|-------|-------------------|
| ECR | ~1GB image storage | ~$0.10 |
| Lambda | 1 run/day × ~65s avg × 1GB memory × 30 days ≈ 1,950 GB-seconds (within free tier) | ~$0.00 |
| **Total** | | **~$0.10/month** |

### Summarizer Pipeline (new)

| Service | Usage | Est. Monthly Cost |
|---------|-------|-------------------|
| ECR | ~2-3GB additional image storage | ~$0.20-0.30 |
| Starter Lambda | Seconds/day, negligible memory | ~$0.00 |
| Summarizer Lambda | Seconds/day, negligible memory | ~$0.00 |
| Watchdog Lambda | Seconds/day, negligible memory | ~$0.00 |
| SNS | ~30 messages/month | ~$0.00 |
| EC2 `g4dn.xlarge` compute | ~10 min/day × 30 days = ~5 hrs/month @ $0.736/hr | ~$3.68 |
| EBS gp3 storage (40GB, always-on) | 40GB × $0.08/GB/month | ~$3.20 |
| CloudWatch Logs | ~7MB/month total across all Lambdas + EC2 (within 5GB free tier) | ~$0.00 |
| Data transfer | Lambda ↔ EC2 (same region/VPC), EC2 → MongoDB Atlas (<100GB/month free) | ~$0.00 |
| **Total** | | **~$7.18/month** |

### Combined Total

| | Monthly Cost |
|--|--|
| Ingestion pipeline | ~$0.10 |
| Summarizer pipeline | ~$7.18 |
| **Grand total** | **~$7.28/month** |

Within the €10/month budget with ~€2-3 headroom.

### Cost Assumptions & Risks

- EC2 compute cost is **variable** — if model load + inference exceeds ~10 min/day, cost climbs. Measure actual runtime in Phase 1 before committing to Phase 3.
- EBS storage is **always-on** regardless of whether the EC2 instance is running — this is unavoidable without deleting and recreating the volume each day, which is not practical.
- NAT Gateway was explicitly ruled out (~$32/month). Public subnet + security group is the chosen approach.
- CloudWatch Logs stay within the free tier at this scale. All log groups must have a **90-day retention policy** set — CloudWatch retains logs forever by default, which silently accumulates storage cost over time. 90 days aligns with the data minimisation principle and is sufficient for incident investigation. No personal data flows through these logs so GDPR does not prescribe a specific retention period, but 90 days is industry standard for operational logs.
- SageMaker costs in Phase 4 are TBD and will be evaluated during that phase.

---

## 14. Out of Scope (This Version)

- Article content fetching (full-text summarization)
- Classification / tagging (separate future model)
- Sentiment analysis (separate future model)
- Frontend display of digests
- Real-time / streaming ingestion
