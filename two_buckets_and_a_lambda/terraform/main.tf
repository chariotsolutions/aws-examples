# An example of S3 file handling using Lambdas

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 3.40.0"
    }
    archive = {
      source = "hashicorp/archive"
    }
  }
}

locals {
    aws_account_id  = data.aws_caller_identity.current.account_id
# xxx figure out how to handle region correctly (emaied Keith)
    aws_region      = data.aws_region.current.name
    bucket_name_base = "com-chariotsolutions-emortontf"
}

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}


