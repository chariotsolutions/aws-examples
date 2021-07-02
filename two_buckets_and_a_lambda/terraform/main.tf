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

provider "aws" {
  region = var.aws_region
}

locals {
    aws_account_id  = data.aws_caller_identity.current.account_id
# xxx reconcile this with the variable of the same name
    aws_region      = data.aws_region.current.name
    bucket_name_base = "com-chariotsolutions-emortontf"
}
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

output "utterance-from-main" {
#  value = "Hello, World!"
#  value = "the region is ${data.aws_region.current.name}"
  value = "the Region is ${local.aws_region}"
}
