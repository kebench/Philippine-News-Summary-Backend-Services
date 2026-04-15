provider "aws" {
  region = "eu-west-1"
}

module "ecr" {
  source               = "../../../modules/ecr"
  repository_name      = var.repository_name
  image_tag_mutability = var.image_tag_mutability
  scan_on_push         = var.scan_on_push
}

module "lambda" {
  source                = "../../../modules/lambda_image"
  function_name         = var.function_name
  image_uri             = var.image_uri
  timeout               = var.timeout
  memory                = var.memory
  ephemeral_storage     = var.ephemeral_storage
  environment_variables = var.environment_variables
  role_name             = var.role_name
  role_path             = var.role_path
  policy_arn            = var.policy_arn
}

module "scheduler" {
  source               = "../../../modules/scheduler"
  schedule_name        = var.schedule_name
  schedule_expression  = var.schedule_expression
  max_attempts         = var.max_attempts
  lambda_function_arn  = module.lambda.function_arn
  lambda_function_name = module.lambda.function_name
  enabled              = var.enabled
  scheduler_role_name  = var.scheduler_role_name
  scheduler_role_path  = var.scheduler_role_path
  policy_arn = var.scheduler_policy_arn
  maximum_window_in_minutes = var.maximum_window_in_minutes
}