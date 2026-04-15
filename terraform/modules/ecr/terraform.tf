# No backend provider configuration is defined in this module. 
# The provider is defined in the root module to allow for better modularity and reusability of the code. 
# By defining the provider in the root module, we can ensure that all modules use the same provider configuration, which makes it easier to manage and maintain the infrastructure as code.
# This also allows us to avoid duplication of provider configurations across multiple modules, making our code cleaner and more efficient.
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws",
      version = "~> 6.37"
    }
  }

  required_version = ">= 1.10"
}