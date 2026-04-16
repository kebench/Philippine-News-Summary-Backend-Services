terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws",
      version = "~> 6.37"
    }
  }

  backend "s3" {
    bucket       = "ph-news-prod-terraform-state"
    key          = "prod/ingestion/terraform.tfstate"
    region       = "eu-west-1"
    use_lockfile = true
  }
  required_version = ">= 1.10"
}