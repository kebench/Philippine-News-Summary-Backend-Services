# ADR-003 — Infrastructure as Code: Terraform

**Date:** 2026-04-14  
**Status:** Accepted  
**Author:** Kevin

---

## Context

The ingestion pipeline was manually provisioned via the AWS console. As the project grows to include the summarizer pipeline and future components (classifier, sentiment model), manual provisioning becomes unsustainable — it is not reproducible, not auditable, and not consistent across environments. A formal Infrastructure as Code (IaC) tool is needed to manage all AWS resources going forward.

This ADR captures the choice of IaC tool, the state management strategy, project structure, naming conventions, environment strategy, CI/CD integration plan, and what is explicitly out of scope.

---

## Decision 1 — Terraform as the IaC Tool

### What was decided
All `ph-news-backend` AWS infrastructure is managed via **Terraform**, retroactively including the ingestion pipeline.

### Why
- Industry standard — the most widely adopted IaC tool, skills transfer directly to professional work
- Cloud-agnostic — works across AWS, GCP, Azure, and third-party providers (e.g. MongoDB Atlas, Vercel) under one toolchain if needed in the future
- Handles the full `ph-news-backend` stack cleanly — Lambda, EC2, VPC, SQS, SNS, ECR, EventBridge, IAM
- Large community, extensive documentation, and mature AWS provider

### Alternatives considered
- **AWS SAM:** Rejected — serverless-focused, handles EC2, VPC, and SQS poorly. Too limited for the summarizer stack.
- **AWS CDK:** Closest alternative — compelling because it uses Python, staying in the same language as the application code. Rejected because it generates CloudFormation underneath, resulting in slower deployments and harder debugging. AWS-only, which limits future flexibility.
- **Pulumi:** Rejected — smaller community, less industry adoption, less mature than Terraform.
- **AWS CloudFormation:** Rejected — verbose, slow, and painful to write and debug directly.

---

## Decision 2 — Remote Backend: S3 with Native Locking

### What was decided
Terraform state is stored remotely in an **S3 bucket** with state locking via **S3 native locking** (`use_lockfile = true`).

```
S3 bucket: ph-news-prod-terraform-state
```

This bucket is the first resource provisioned — manually, once — before any other Terraform is written. Everything else is managed by Terraform thereafter.

### Why
- Local state is fragile — loss of the state file means Terraform loses track of all provisioned resources
- Remote state is the industry standard even for solo projects
- S3 native locking (`use_lockfile = true`) prevents state corruption if `terraform apply` is ever run concurrently — no additional resources required
- S3 versioning enabled on the state bucket — allows rollback to a previous state if needed
- DynamoDB-based locking was originally planned but is **deprecated as of Terraform 1.10+** and will be removed in a future version — S3 native locking is the correct forward-looking choice

### Cost
- S3: negligible — state files are small, costs cents per month
- No DynamoDB table needed — eliminates an additional resource and its associated cost

### Alternatives considered
- **S3 + DynamoDB locking:** Originally planned, rejected after implementation — DynamoDB-based locking is deprecated in Terraform 1.10+ and will be removed in a future minor version. Migrating away from it later is unnecessary overhead.

---

## Decision 3 — Module-Per-Service Structure

### What was decided
Terraform code is organised into **reusable modules per infrastructure type** and **service-level configurations** that compose those modules.

```
terraform/
├── modules/
│   ├── lambda/          # reusable Lambda + IAM role module
│   ├── ec2/             # reusable EC2 + EBS + security group module
│   ├── sqs_sns/         # reusable SNS topic + SQS queue + DLQ module
│   ├── vpc/             # reusable VPC + subnet module
│   └── ecr/             # reusable ECR repository module
├── environments/
│   └── prod/
│       ├── ingestion/
│       │   └── main.tf  # ingestion stack — composes modules
│       └── summarizer/
│           └── main.tf  # summarizer stack — composes modules
└── bootstrap/
    └── main.tf          # S3 state bucket (provisioned once manually)
```

### Why
- Each service is independently deployable — changes to the summarizer stack do not risk the ingestion stack
- Reusable modules reduce duplication — a Lambda module written once is used by ingestion, starter, summarizer, and watchdog
- Easier to debug, maintain, and extend — consistent with the modular design philosophy applied to application code

---

## Decision 4 — Naming Convention

### What was decided
All AWS resources follow a consistent naming convention:

```
{project}-{environment}-{service}-{resource}
```

Examples:
```
ph-news-prod-ingestion-lambda
ph-news-prod-summarizer-ec2
ph-news-prod-summarizer-sqs
ph-news-prod-summarizer-starter-lambda
ph-news-prod-watchdog-lambda
ph-news-prod-terraform-state        (S3 bucket)
```

### Why
- Consistent naming makes IAM policies, CloudWatch log filters, and cost allocation straightforward
- Environment prefix (`prod`) makes it immediately clear which environment a resource belongs to
- Prevents accidental cross-environment resource references

---

## Decision 5 — Environment Strategy

### What was decided
Two environments: **local** and **prod**.

- **Local** acts as the development environment — `terraform plan` is run locally to validate changes before applying
- **Prod** is the live environment — `terraform apply` targets prod AWS resources
- No separate AWS dev environment is provisioned — the cost overhead is not justified for a solo project at this scale

### Why
- A separate AWS dev environment would roughly double infrastructure costs — not acceptable within the €10/month budget
- For a solo developer on a daily batch job, the risk of applying directly to prod (after local validation) is acceptable and recoverable
- `terraform plan` output serves as the safety check before every `terraform apply`

### What was traded off
- No environment isolation at the AWS resource level — a bad `terraform apply` affects live infrastructure directly
- Mitigated by always running `terraform plan` first and reviewing output carefully before applying

---

## Decision 6 — CI/CD Integration

### What was decided
Terraform is run **manually from the local machine** for now. The target state is **GitHub Actions** for automated deployment.

**Current (Phase 1-3):**
```
Local machine
    └── terraform plan    # validate changes
    └── terraform apply   # apply to prod
```

**Target (Phase 3+):**
```
GitHub Actions
    ├── PR opened → terraform plan (output posted to PR)
    └── Merge to main → terraform apply (deploy to prod)
```

### Why
- GitHub Actions is the industry standard for CI/CD — aligns with the project goal of mirroring production practices
- Starting with manual apply keeps complexity low during early phases while the infrastructure is being defined and iterated on
- Migration from manual to GitHub Actions is a clean, isolated change when the time comes — it will warrant ADR-004

---

## Decision 7 — Sensitive Variables Handling

### What was decided
Secrets and credentials are **never stored in `.tf` files or committed to version control**. They are passed via:
- AWS credentials: `~/.aws/credentials` profile locally, GitHub Actions secrets in CI/CD
- Sensitive Terraform variables: `terraform.tfvars` file (gitignored) locally, GitHub Actions secrets in CI/CD

A `.gitignore` entry covers all sensitive files:
```
*.tfvars
*.tfstate
*.tfstate.backup
.terraform/
```

### Why
- Credentials in version control is a critical security vulnerability regardless of project size
- `.tfvars` gitignored is the Terraform community standard for handling environment-specific sensitive values
- State files are gitignored because they can contain sensitive resource metadata and are managed remotely via S3

---

## Decision 8 — Version Locking

### What was decided
Terraform version and AWS provider version are **pinned explicitly** in every module and service configuration from day one.

```hcl
terraform {
  required_version = ">= 1.9.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}
```

### Why
- Unpinned versions cause silent breaking changes when Terraform or the AWS provider is upgraded
- `.terraform.lock.hcl` is committed to version control — ensures all environments use identical provider versions

---

## Decision 9 — Out of Scope

The following are explicitly not managed by this Terraform setup:

| Resource | Reason |
|----------|--------|
| MongoDB Atlas | Separate provider, managed independently. May be added in a future ADR if Atlas Terraform provider is adopted. |
| Vercel (frontend) | Managed via Vercel's own deployment pipeline |
| DNS / domain management | Not yet in scope for this project |
| GitHub repository settings | Managed manually |

---

## Decision 10 — Existing Ingestion Infrastructure

### What was decided
Existing manually-provisioned ingestion resources are **imported into Terraform state** via `terraform import`. They are not torn down and reprovisioned.

### Why
- Zero downtime — the live ingestion pipeline continues running uninterrupted during the import process
- `terraform import` brings existing resources under Terraform state management without modifying them
- Requires writing Terraform config that exactly matches the existing manually-provisioned resources before importing

### Process
```
1. Write Terraform config matching existing ingestion resources exactly
2. terraform plan — confirm zero diff before importing
3. terraform import — bring each resource under state management
4. terraform plan again — confirm clean plan with no changes
```

---

## Consequences

- The `bootstrap/` directory must be applied manually once before any other Terraform is run — the S3 state bucket must exist before the remote backend can be configured
- All future infrastructure changes go through Terraform — no manual AWS console provisioning from this point forward
- ADR-004 will be written when GitHub Actions CI/CD is implemented for automated Terraform deployment
- Ingestion pipeline refactor (code structure) should be completed before the Terraform import to avoid importing resources that will immediately need updating
- IAM permissions carry a privilege escalation risk via `iam:AttachRolePolicy`. Permission boundaries on all `ph-news-*` roles should be implemented before moving to production