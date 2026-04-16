# ECR
variable "repository_name" {
  description = "The name of the ECR repository"
  type        = string
}

variable "image_tag_mutability" {
  description = "The tag mutability setting for the ECR repository"
  type        = string
}

variable "scan_on_push" {
  description = "Flag for scanning images for vulnerabilities on push"
  type        = bool
}

# Lambda
variable "function_name" {
  description = "The name of the Lambda function"
  type        = string
}

variable "image_uri" {
  description = "The full ECR image URI including the tag for the Lambda"
  type        = string
}

variable "timeout" {
  description = "The timeout setting for the Lambda function in seconds"
  type        = number
}

variable "memory" {
  description = "The memory allocated in MB for the Lambda function"
  type        = number
}

variable "ephemeral_storage" {
  description = "The ephemeral storage size in MB for the Lambda function"
  type        = number
}

variable "environment_variables" {
  description = "A map of environment variables to set for the Lambda function"
  type        = map(string)
  sensitive   = true
}

# Scheduler
variable "schedule_name" {
  description = "The name of the EventBridge scheduler schedule"
  type        = string
}

variable "schedule_expression" {
  description = "The cron or rate expression for the scheduler"
  type        = string
}

variable "max_attempts" {
  description = "The maximum number of retry attempts for the scheduler target"
  type        = number
}

variable "enabled" {
  description = "Whether the scheduler schedule is enabled"
  type        = bool
}

variable "role_name" {
  description = "The name of the IAM role to be created for Lambda execution"
  type        = string
}

variable "role_path" {
  description = "The path for the IAM role"
  type        = string
}

variable "policy_arn" {
  description = "The ARN of the IAM policy to attach to the Lambda execution role"
  type        = string
}

variable "scheduler_role_name" {
  description = "The name of the IAM role to be created for EventBridge scheduler execution"
  type        = string
}

variable "scheduler_role_path" {
  description = "The path for the IAM role for EventBridge scheduler execution"
  type        = string
}

variable "scheduler_policy_arn" {
  description = "The ARN of the IAM policy to attach to the EventBridge scheduler execution role"
  type        = string
}

variable "maximum_window_in_minutes" {
  description = "The maximum window in minutes for the EventBridge scheduler schedule"
  type        = number
}

variable "image_retention_count" {
  description = "The number of images to retain in the ECR repository"
  type       = number
}