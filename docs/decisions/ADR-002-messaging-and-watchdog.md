# ADR-002 — Messaging Pattern and Watchdog Trigger

**Date:** 2026-04-13  
**Status:** Accepted  
**Author:** Kevin  
**Supersedes:** Portions of ADR-001 Decision 2 (SNS-only trigger for Summarizer Lambda)

---

## Context

During architecture diagram review, two decisions from ADR-001 were revisited and refined. ADR-001 Decision 2 described EC2 publishing a ready event to SNS which directly triggered the Summarizer Lambda. This was updated after evaluating retry behaviour, failure handling, and future extensibility requirements. Additionally, the Watchdog Lambda trigger mechanism was discussed and a final approach selected.

---

## Decision 1 — SNS → SQS (Not SNS Alone)

### What was decided
EC2 publishes its ready event to **SNS**, which fans out to an **SQS queue**. The Summarizer Lambda is triggered by SQS, not SNS directly.

```
EC2 (boots + loads model)
    └── publishes ready event to SNS
            └── SNS fans out to SQS queue
                    └── SQS triggers Summarizer Lambda
```

### Why
- SNS alone is fire-and-forget — if the Summarizer Lambda fails to process the message, SNS does not retry and provides no failure visibility
- SQS provides **automatic retries** and a **Dead Letter Queue (DLQ)** — if the Summarizer Lambda fails, the message is retried up to a configured limit, then parked in the DLQ
- CloudWatch can alarm on DLQ depth — giving failure alerting that SNS alone cannot provide
- The SNS → SQS pattern preserves **fan-out capability** — future consumers (classifier, sentiment model) each get their own SQS queue subscribed to the same SNS topic, without modifying EC2 or existing queues

### What was traded off
- Slightly more infrastructure — one SNS topic + one SQS queue instead of SNS alone
- Marginal cost increase — negligible at this scale (both within AWS free tier at 30 messages/month)

### Alternatives considered
- **SQS alone (no SNS):** Rejected — loses fan-out capability. When the classifier is added, a second SQS queue cannot subscribe directly to the first. Would require a separate publish mechanism.
- **SNS alone:** Rejected — no retry, no DLQ, no failure visibility. Fire-and-forget is insufficient for a pipeline where EC2 costs money if left running.
- **SNS → SQS (chosen):** Best of both — fan-out from SNS, reliability from SQS.

---

## Decision 2 — Watchdog Lambda Triggered by EventBridge Schedule (Option 1)

### What was decided
The Watchdog Lambda is triggered by an **EventBridge scheduled rule** that fires every X minutes. On each invocation, the Watchdog Lambda **checks EC2 state first** — if the instance is not running, it exits immediately. If the instance has been running longer than the configured threshold, it force-stops it.

```
EventBridge (every X minutes)
    └── Watchdog Lambda
            ├── EC2 not running → exit immediately
            └── EC2 running > threshold → force-stop
```

### Why
- The Watchdog must be **fully independent** of the Summarizer Lambda — it exists specifically to catch cases where the Summarizer Lambda crashes or fails to stop EC2
- A Summarizer-triggered Watchdog defeats the purpose — if Summarizer crashes, it never triggers the Watchdog, which is exactly the failure case the Watchdog is designed for
- The early-exit check (EC2 not running → exit immediately) makes the constant polling effectively free — Lambda execution is milliseconds long when EC2 is stopped, well within the free tier
- Simple, reliable, no additional infrastructure required

### Threshold
The exact threshold (X minutes) is deferred to **OQ-05** in the planning document. It will be set based on real EC2 boot + model load + inference time measured during Phase 1, with a comfortable safety margin above the measured runtime.

### Alternatives considered
- **Summarizer Lambda triggers Watchdog:** Rejected — Watchdog is never triggered on the failure path where it is needed most
- **Starter Lambda enables EventBridge rule, Summarizer disables it:** Rejected — adds responsibility to both Lambdas, rule stays enabled forever if Summarizer crashes
- **EventBridge EC2 state change event (Option 3):** More elegant — truly event-driven, no polling. Deferred to a future phase once the pipeline is stable and the basic flow is validated. This is the target architecture for Phase 3+.

---

## Consequences

- A DLQ must be provisioned alongside the SQS queue — CloudWatch alarm on DLQ depth is the primary failure alerting mechanism for the Summarizer Lambda
- The Watchdog threshold (OQ-05) must be set after Phase 1 measurements — do not guess
- Option 3 (EventBridge EC2 state change) remains the target for the Watchdog trigger in a future phase — this will warrant ADR-003 when implemented
- ADR-001 Decision 2 flow diagram should be read in conjunction with this ADR — the SNS → SQS pattern supersedes the SNS-only reference in that decision
- All infrastructure described in this ADR (SNS, SQS, DLQ) is managed via Terraform. See ADR-003.