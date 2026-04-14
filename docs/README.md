# ph-news-backend — Documentation

This folder contains planning documents, architecture references, and decision records for the `ph-news-backend` project.

---

## Structure

```
docs/
├── architecture/
│   ├── ingestion-pipeline.md                  # Ingestion pipeline — requirements, tech stack, design
│   ├── ingestion-architecture.png             # Ingestion system architecture diagram (TBD)
│   ├── summarizer-pipeline.md                 # Summarizer pipeline — requirements, tech stack, design
│   └── summarizer-architecture.png            # Summarizer system architecture diagram (v3.1)
└── decisions/
    ├── ADR-001-summarizer-arch.md             # Initial summarizer architecture decisions
    └── ADR-002-messaging-and-watchdog.md      # SNS → SQS pattern and Watchdog trigger
```

---

## Components

| Component | Status | Document |
|-----------|--------|----------|
| Ingestion pipeline | ✅ Live (v0.1.1) | [architecture/ingestion-pipeline.md](architecture/ingestion-pipeline.md) |
| Summarizer pipeline | 🔵 Planning (v0.1.0-draft) | [architecture/summarizer-pipeline.md](architecture/summarizer-pipeline.md) |
| Classifier | ⬜ Not started | TBD |
| Sentiment analysis | ⬜ Not started | TBD |

---

## Architecture Decision Records (ADRs)

ADRs capture *why* decisions were made, not just what was decided. Read these before changing anything significant.

| ADR | Decision | Status |
|-----|----------|--------|
| [ADR-001](decisions/ADR-001-summarizer-arch.md) | Summarizer pipeline architecture — microservices, VPC design, model hosting, log retention | Partially superseded by ADR-002 |
| [ADR-002](decisions/ADR-002-messaging-and-watchdog.md) | Messaging pattern (SNS → SQS) and Watchdog Lambda trigger | Accepted |
