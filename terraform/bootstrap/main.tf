terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws",
      version = "~> 6.37"
    }
  }

  required_version = ">= 1.4"
}

provider "aws" {
  region = "eu-west-1"
}

# S3 Bucket for Terraform State Storage
resource "aws_s3_bucket" "ph_news_state" {
  bucket = "ph-news-prod-terraform-state"

  lifecycle {
    prevent_destroy = true
  }
}

#S3 Versioning
resource "aws_s3_bucket_versioning" "ph_news_state_versioning" {
  bucket = aws_s3_bucket.ph_news_state.id

  versioning_configuration {
    status = "Enabled"
  }
}

# S3 Server-Side Encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "ph_news_state_encryption" {
  bucket = aws_s3_bucket.ph_news_state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# S3 Public Access Block
resource "aws_s3_bucket_public_access_block" "ph_news_state_public_access_block" {
  bucket = aws_s3_bucket.ph_news_state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}