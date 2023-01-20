##
## Creates several SQS queues with related resources, using a module,
## then combines their policies into a role.
## 

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 4.0.0"
    }
  }
}

data "aws_region" "current" {}


module "foo_queue" {
  source = "./modules/create_sqs"
  queue_name = "Foo"
}


module "bar_queue" {
  source = "./modules/create_sqs"
  queue_name = "Bar"
}


module "baz_queue" {
  source = "./modules/create_sqs"
  queue_name = "Baz"
  retry_count = 5
}


resource "aws_iam_role" "application_role" {
  name        = "Example-${data.aws_region.current.name}"
  description = "Created by Terraform SQS module example"

  assume_role_policy = jsonencode({
    "Version"   = "2012-10-17",
    "Statement" = [
      {
        "Effect"    = "Allow"
        "Action"    = "sts:AssumeRole"
        "Principal" = { "Service" = "ec2.amazonaws.com" }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "application_role_foo_producer" {
  role       = aws_iam_role.application_role.name
  policy_arn = module.foo_queue.producer_policy_arn
}

resource "aws_iam_role_policy_attachment" "application_role_bar_producer" {
  role       = aws_iam_role.application_role.name
  policy_arn = module.bar_queue.producer_policy_arn
}

resource "aws_iam_role_policy_attachment" "application_role_baz_producer" {
  role       = aws_iam_role.application_role.name
  policy_arn = module.baz_queue.producer_policy_arn
}
