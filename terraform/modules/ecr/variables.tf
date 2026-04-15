variable "repository_name" {
  description = "the name of the ECR repository"
  type        = string
}

variable "image_tag_mutability" {
  description = "the tag mutability setting for the ECR repository"
  type        = string
}

variable "scan_on_push" {
  description = "flag for scanning images for vulnerabilities on push"
  type = bool
}