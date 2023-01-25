terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 4.0.0"
    }
  }
}

provider "aws" {
}


data "aws_caller_identity" "current" {}
data "aws_region" "current" {}


locals {
  aws_account_id  = data.aws_caller_identity.current.account_id
  aws_region      = data.aws_region.current.name
}
