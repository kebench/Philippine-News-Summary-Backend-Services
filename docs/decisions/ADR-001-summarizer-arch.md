# ADR-001 — Summarizer Pipeline Architecture

**Date:** 2026-03-23  
**Status:** Accepted  
**Author:** Kevin

---

## Context

The `ph-news-summarizer` component needs to group and summarise daily ingested headlines into a structured digest. Several architectural decisions were made during the planning phase. This document captures what was decided and why, so future contributors (or future Kevin) understand the reasoning behind the design.

---

## Decision 1 — Headline Digest, Not Full-Article Summarisation

### What was decided
The summarizer operates on **headline text only** — no article content fetching. It groups semantically related headlines into topic clusters and generates a 1–2 sentence narrative per cluster, similar to a news briefing.

### Why
- Full-article fetching adds significant complexity (HTTP fetching, content extraction, rate limiting per publisher)
- Headline-level digests are sufficient for the use case — grouping and narrating themes, not reproducing article content
- Classification and sentiment analysis are separate future models; this component does one thing

### Alternatives considered
- Fetch full article content via `httpx` + BeautifulSoup — rejected for complexity and scope creep

---

## Decision 2 — Microservices Pipeline (Option C)

### What was decided
The summarizer is built as a **microservices pipeline** using the following services:

```
Ingestion Lambda
    └── Starter Lambda          # starts EC2, exits immediately
            └── EC2 (boots, loads model, publishes SNS ready event)
                    └── Summarizer Lambda   # triggered by SNS
                            ├── calls EC2 inference
                            ├── stores HeadlineDigest in MongoDB
                            └── stops EC2
                                    └── Watchdog Lambda (EventBridge safety net)
```

### Why
- Each service has a single, clearly defined responsibility — when something fails, CloudWatch immediately tells you which service it was
- No Lambda sits idle waiting for EC2 to boot — the SNS trigger is event-driven
- Extensible — future consumers (classifier, sentiment model) subscribe to the same SNS topic without modifying existing services
- Mirrors how production MLE pipelines are built; supports the learning goal of the project

### Alternatives considered
- **Option A — Summarizer Lambda handles start/stop itself:** Simpler, but Lambda pays for idle EC2 boot wait time. EC2 stays on if Lambda crashes. Not reusable.
- **Option B — Dedicated Starter and Stopper Lambdas:** Better separation, but still a synchronous invocation chain. Stopper must be reliably called even on failure.
- **Option C (chosen):** Event-driven, no idle wait, naturally extensible. Added complexity is justified by learning goals and future extensibility.

---

## Decision 3 — EC2 is On-Demand, Not Always-On

### What was decided
The EC2 inference instance is **started by the Starter Lambda and stopped by the Summarizer Lambda** after each run. It is not kept running between daily jobs.

### Why
- The pipeline runs once per day for ~10 minutes. Keeping EC2 on 24/7 would cost ~$22/month in compute alone — for a job that runs 0.7% of the time.
- EBS storage (~$3.20/month) is unavoidable as the volume persists model weights between runs, but compute cost is contained.

---

## Decision 4 — Public Subnet + Security Group (Not Private Subnet + NAT Gateway)

### What was decided
The EC2 inference instance is placed in a **public subnet** with a strict security group:
- Inbound port 8000: Summarizer Lambda security group only
- Inbound port 22: Developer IP only
- Outbound: all (MongoDB Atlas, SNS, model downloads)

### Why
- NAT Gateway costs ~$32/month always-on — completely disproportionate for a daily batch job within a €10/month budget
- NAT Instance (legacy EC2-based NAT) was ruled out — deprecated by AWS, single point of failure, not worth the ops burden
- A strict security group on a public subnet provides ~90% of the security benefit of a private subnet at a fraction of the cost and zero maintenance overhead
- The pipeline processes no personal data — the risk profile does not justify private subnet cost

### What was traded off
- Network-level isolation (private subnet) is sacrificed for cost and simplicity
- This decision should be revisited if the project moves toward a production or multi-user workload

### Alternatives considered
- Private subnet + NAT Gateway: ~$32/month, rejected on cost grounds
- Private subnet + NAT Instance: ~$7/month but deprecated tech, single point of failure, rejected

---

## Decision 5 — Self-Hosted Open-Source Model (Not External API)

### What was decided
The summarizer uses a **self-hosted open-source model** (Llama 3.1 8B or Mistral 7B) served via vLLM, rather than calling an external LLM API (e.g. Claude, OpenAI).

### Why
- The primary learning goal of this component is the **full MLE lifecycle** — model serving, fine-tuning, and deployment
- Calling an external API would skip the most valuable learning surface entirely
- At 16GB VRAM (RTX 5070 Ti), Llama 3.1 8B at fp16 fits comfortably — no compromise on model quality is needed locally
- Long-term cost: a self-hosted model on EC2 for ~5 hrs/month is cheaper than per-token API pricing at scale

### Alternatives considered
- Claude API / OpenAI API: faster to ship but defeats the learning goal entirely

---

## Decision 6 — 90-Day CloudWatch Log Retention

### What was decided
All Lambda and EC2 CloudWatch log groups are configured with a **90-day retention policy**.

### Why
- CloudWatch retains logs indefinitely by default — storage silently accumulates over time
- 90 days is sufficient for debugging and incident investigation
- The pipeline processes no personal data, so GDPR does not prescribe a specific retention period; 90 days aligns with the data minimisation principle
- Good operational hygiene regardless of cost impact

---

## Consequences

- The microservices design introduces more moving parts than a single Lambda approach — distributed tracing (CloudWatch correlation IDs or AWS X-Ray) will be important in Phase 3
- The public subnet decision must be documented and revisited at Phase 3 before any production consideration
- EC2 boot + model load time must be measured in Phase 1 (local) to validate the cost estimate and set the Watchdog threshold correctly
- All infrastructure described in this ADR is managed via Terraform. See ADR-003.
