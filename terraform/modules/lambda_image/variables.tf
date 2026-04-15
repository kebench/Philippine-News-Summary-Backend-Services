variable "function_name" {
  description = "the name of the Lambda function"
  type        = string
}

variable "image_uri" {
  description = "the full ECR image URI including the tag for the Lambda"
  type        = string
}

variable "timeout" {
  description = "the timeout setting for the Lambda function"
  type        = number
}

variable "memory" {
  description = "the memory allocated in MB"
  type        = number
}

variable "environment_variables" {
  description = "a map of environment variables to set for the Lambda function"
  type        = map(string)
  sensitive   = true
}

variable "ephemeral_storage" {
  description = "the ephemeral storage size in MB for the Lambda function"
  type        = number
}

variable "role_name" {
  description = "the name of the IAM role to be created for Lambda execution"
  type        = string
}

variable "role_path" {
  description = "the path for the IAM role"
  type        = string
}

variable "policy_arn" {
  description = "the ARN of the IAM policy to attach to the Lambda execution role"
  type        = string
}