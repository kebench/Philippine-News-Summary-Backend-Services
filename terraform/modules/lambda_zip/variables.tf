variable "function_name" {
  description = "the name of the Lambda function"
  type        = string
}

variable "filename" {
  description = "the path to the ZIP file for the Lambda function"
  type        = string
}

variable "handler" {
  description = "the handler for the Lambda function (e.g., handler.lambda_handler)"
  type        = string
}

variable "runtime" {
  description = "the runtime environment for the Lambda function (e.g., nodejs14.x)"
  type        = string
}

variable "source_code_hash" {
  description = "the base64-encoded SHA256 hash of the ZIP file for the Lambda function"
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