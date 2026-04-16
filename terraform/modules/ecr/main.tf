# Providers aren't defined in this module, but in the root module. This allows us to reuse the same provider configuration across multiple modules.
# If we defined the provider here, it would be isolated to this module and we wouldn't be able to use it in other modules without redefining it.
# By not defining the provider here, we can ensure that all modules use the same provider configuration defined in the root module.

resource "aws_ecr_repository" "ecr_repository" {
  name                 = var.repository_name
  image_tag_mutability = var.image_tag_mutability
  image_scanning_configuration {
    scan_on_push = var.scan_on_push
  }

}

resource "aws_ecr_lifecycle_policy" "policy" {
  repository = aws_ecr_repository.ecr_repository.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep only the latest image"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = var.image_retention_count
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

