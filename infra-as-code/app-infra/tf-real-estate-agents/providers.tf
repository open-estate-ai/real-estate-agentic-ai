terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "6.12.0"
    }
  }
  backend "local" {
  }
}


# The default AWS Provider
provider "aws" {
  region = var.resource_region
  default_tags {
    tags = var.default_tags
  }
}
