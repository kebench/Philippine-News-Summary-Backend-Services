# Terraform Import Guide

This guide documents the correct sequence and approach for importing existing AWS resources into Terraform state. Follow this whenever bringing manually-provisioned resources under Terraform management.

---

## Why Import Order Matters

Terraform imports resources into state independently — it does not automatically resolve dependencies during import. If you import a resource that references another resource not yet in state, Terraform may error or produce incorrect plans.

Always import in **dependency order** — import what others depend on first.

---

## General Import Sequence

```
1. IAM Roles
   └── Must exist in state before policies can be attached

2. IAM Policy Attachments / Inline Policies
   └── Must exist before resources that assume the role

3. Supporting Resources (S3, DynamoDB, SNS, SQS, ECR, VPC, etc.)
   └── Must exist before resources that reference them

4. Primary Resources (Lambda, EC2, Scheduler, etc.)
   └── Import last — depends on everything above
```

---

## General Rules

- **Roles before policies** — you cannot attach a policy to a role that does not exist in state yet
- **Policies before resources** — resources assume roles, roles need policies first
- **Dependencies before dependents** — if resource A references resource B, import B first
- **Check AWS console first** — auto-generated names, paths, and ARNs often differ from what Terraform expects
- **Run `terraform plan` after every import** — catch drift immediately rather than at the end
- **Match config exactly before importing** — Terraform compares imported state against your config. If they differ, the next plan will show unwanted changes or replacements

---

## Common Gotchas

### Auto-generated resource names
AWS auto-generates names with random suffixes for roles and policies created via the console (e.g. `ph-news-ingestion-role-yia396fa`). These won't match your Terraform naming convention. Add `role_name` and `role_path` variables to your module so the config can match the existing resource exactly.

### Service role paths
Roles created by AWS services (Lambda, EventBridge Scheduler) are placed under `/service-role/` path, not the root `/` path. Your IAM policy ARN must include the correct path:
```
arn:aws:iam::ACCOUNT_ID:role/service-role/ph-news-*
```

### Inline vs attached policies
AWS console-created resources often have **attached managed policies** (custom or AWS-managed), not inline policies. Check with:
```powershell
# Check inline policies
aws iam list-role-policies --role-name ROLE_NAME

# Check attached policies
aws iam list-attached-role-policies --role-name ROLE_NAME
```
Use `aws_iam_role_policy_attachment` for attached policies, `aws_iam_role_policy` for inline policies.

### Trust policy conditions
Roles auto-created by AWS services may include a `Condition` block in the assume role policy (e.g. `aws:SourceAccount`). If your Terraform config omits it, the plan will show unwanted drift. Match it exactly.

### Import ID formats
Each resource type has a specific import ID format. Common ones:

| Resource | Import ID Format |
|----------|-----------------|
| `aws_iam_role` | `role-name` |
| `aws_iam_role_policy_attachment` | `role-name/policy-arn` |
| `aws_iam_role_policy` | `role-name:policy-name` |
| `aws_ecr_repository` | `repository-name` |
| `aws_lambda_function` | `function-name` |
| `aws_scheduler_schedule` | `group-name/schedule-name` |
| `aws_s3_bucket` | `bucket-name` |
| `aws_dynamodb_table` | `table-name` |

---

## Ingestion Pipeline Import Sequence

For reference — the sequence used to import the `ph-news-ingestion` pipeline:

```
1. aws_ecr_repository
   terraform import module.ecr.aws_ecr_repository.ecr_repository ph-news-ingestion

2. aws_iam_role (Lambda execution role)
   terraform import module.lambda.aws_iam_role.lambda_execution_role ph-news-ingestion-role-yia396fa

3. aws_iam_role_policy_attachment (Lambda logging policy)
   terraform import module.lambda.aws_iam_role_policy_attachment.lambda_basic_execution \
   ph-news-ingestion-role-yia396fa/arn:aws:iam::ACCOUNT_ID:policy/service-role/AWSLambdaBasicExecutionRole-0cbc2850-50db-438b-9134-ef40bc2edac9

4. aws_lambda_function
   terraform import module.lambda.aws_lambda_function.lambda_function ph-news-ingestion

5. aws_iam_role (Scheduler role)
   terraform import module.scheduler.aws_iam_role.scheduler_role \
   Amazon_EventBridge_Scheduler_LAMBDA_ee70377cf3

6. aws_iam_role_policy_attachment (Scheduler policy)
   terraform import module.scheduler.aws_iam_role_policy_attachment.scheduler_policy \
   Amazon_EventBridge_Scheduler_LAMBDA_ee70377cf3/arn:aws:iam::ACCOUNT_ID:policy/service-role/Amazon-EventBridge-Scheduler-Execution-Policy-08805fa6-ee06-4c82-9c61-2563459e2773

7. aws_scheduler_schedule
   terraform import module.scheduler.aws_scheduler_schedule.schedule \
   default/ph-news-ingestion-schedule
```

---

## After All Imports

Run `terraform plan` — the goal is the cleanest plan possible:

- `0 to add` for all imported resources
- Only legitimate in-place updates are acceptable (e.g. config improvements like enabling `scan_on_push`)
- **No destroy and recreate (`-/+`)** — this means config doesn't match the imported resource
- **No unexpected destroys (`-`)** — review carefully before proceeding

Once the plan is clean, run `terraform apply`.