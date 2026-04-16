# Terraform Tainted Resources Guide

This guide documents what tainted resources are, why they occur, and how to handle them correctly.

---

## What is a Tainted Resource?

A tainted resource is one that Terraform has marked as potentially broken. On the next `terraform apply`, Terraform will **destroy and recreate** the tainted resource rather than updating it in-place.

Terraform taints a resource when:
- An error occurs **during** a `terraform apply` after the resource was created
- Terraform cannot verify the resource's state after creation (e.g. due to missing IAM permissions)
- A `terraform apply` is interrupted mid-way

---

## How to Identify Tainted Resources

Tainted resources appear in `terraform plan` output with the `-/+` symbol and a note:

```
# module.ecr.aws_ecr_lifecycle_policy.policy is tainted, so must be replaced
-/+ resource "aws_ecr_lifecycle_policy" "policy" {
```

---

## How to Handle a Tainted Resource

**Always verify in AWS first before untainting.**

### Step 1 — Check if the resource actually exists in AWS
Go to the AWS console and confirm whether the resource was actually created.

### Step 2a — Resource exists in AWS → Untaint
If the resource exists and is correctly configured, the taint is a false alarm — usually caused by a permission error during the post-creation read. Untaint it:

```powershell
terraform untaint <resource_address>
```

Example:
```powershell
terraform untaint module.ecr.aws_ecr_lifecycle_policy.policy
```

Then run `terraform plan` to confirm it no longer shows as a replace.

### Step 2b — Resource does not exist in AWS → Leave tainted
If the resource was never actually created, leave it tainted. Terraform will recreate it on the next `terraform apply`.

---

## Common Causes in This Project

| Cause | What Happened | Resolution |
|-------|---------------|------------|
| Missing IAM permission during apply | Resource created but Terraform couldn't read it back | Add the missing permission, untaint, replan |
| Interrupted `terraform apply` | Resource partially created | Check AWS console, untaint if complete, otherwise leave |
| Network error during apply | Same as above | Check AWS console, untaint if complete |

---

## General Rule

```
Resource tainted
    └── Check AWS console
            ├── Resource exists correctly → untaint → terraform plan → terraform apply
            └── Resource does not exist → leave tainted → terraform apply (recreates it)
```

---

## Prevention

The most common cause of taints in this project is **missing IAM permissions**. A resource gets created but Terraform can't read it back to confirm the state.

To prevent this:
- Always run `terraform plan` with a fresh set of permissions before applying to a new resource type
- When adding a new AWS service to Terraform, check the provider docs for all read permissions needed (e.g. `Get*`, `List*`, `Describe*`) and add them to the deploy policy upfront
- Common read permissions needed per service:

| Service | Read Permissions Often Needed |
|---------|------------------------------|
| ECR | `ecr:GetLifecyclePolicy`, `ecr:ListTagsForResource`, `ecr:GetRepositoryPolicy` |
| Lambda | `lambda:ListVersionsByFunction`, `lambda:GetPolicy` |
| IAM | `iam:GetRole`, `iam:ListAttachedRolePolicies`, `iam:ListRolePolicies` |
| Scheduler | `scheduler:GetSchedule`, `scheduler:GetScheduleGroup` |
| S3 | `s3:GetBucketVersioning`, `s3:GetEncryptionConfiguration`, `s3:GetBucketPublicAccessBlock` |