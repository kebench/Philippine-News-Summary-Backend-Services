variable "schedule_name" {
  description = "the name of the EventBridge rule"
  type        = string
}

variable "schedule_expression" {
  description = "the schedule expression for the EventBridge rule"
  type        = string
}

variable "lambda_function_arn" {
  description = "the ARN of the Lambda function to be triggered by the EventBridge rule"
  type        = string
}

variable "lambda_function_name" {
  description = "the name of the lambda function to be triggered by the Eventbridge rule"
  type        = string
}

variable "enabled" {
  description = "whether the EventBridge rule is enabled or not"
  type        = bool
}

variable "max_attempts" {
  description = "the maximum number of retry attempts for the scheduled target"
  type        = number
}

variable "scheduler_role_name" {
  description = "the name of the IAM role to be created for EventBridge scheduler execution"
  type        = string
}

variable "scheduler_role_path" {
  description = "the path for the IAM role for EventBridge scheduler execution"
  type        = string
}

variable "policy_arn" {
  description = "the ARN of the IAM policy to attach to the EventBridge scheduler execution role"
  type        = string
}

variable "maximum_window_in_minutes" {
  description = "the maximum window in minutes for the EventBridge scheduler schedule"
  type        = number
}