resource "aws_scheduler_schedule" "schedule" {
  name       = var.schedule_name
  group_name = "default"

  flexible_time_window {
    mode = "FLEXIBLE"
    maximum_window_in_minutes = var.maximum_window_in_minutes
  }

  schedule_expression = var.schedule_expression

  target {
    arn      = var.lambda_function_arn
    role_arn = aws_iam_role.scheduler_role.arn

    retry_policy {
      maximum_retry_attempts = var.max_attempts
    }
  }
}

resource "aws_iam_role" "scheduler_role" {
  name = var.scheduler_role_name
  path = var.scheduler_role_path

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect    = "Allow"
        Principal = {
          Service = "scheduler.amazonaws.com"
        }
        Action    = "sts:AssumeRole"
        Condition = {
          StringEquals = {
            "aws:SourceAccount" = data.aws_caller_identity.current.account_id
          }
        }
      }
    ]
  })
}

data "aws_caller_identity" "current" {}

resource "aws_iam_role_policy_attachment" "scheduler_policy" {
  role = aws_iam_role.scheduler_role.name
  policy_arn = var.policy_arn
}