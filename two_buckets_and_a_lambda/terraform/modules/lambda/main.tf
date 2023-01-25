##
## A Lambda module that's tailored to our single-source-file deployments.
##

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 4.0.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = ">= 2.3.0"
    }
    local = {
      source  = "hashicorp/local"
      version = ">= 2.3.0"
    }
  }
}


data "aws_region" "current" {}


locals {
  aws_region                  = data.aws_region.current.name
}

data "local_file" "lambda_source" {
  filename    = var.source_file
}


data "archive_file" "deployment_bundle" {
  type        = "zip"
  output_path = "${path.module}/${var.name}.zip"
  source {
    content   = data.local_file.lambda_source.content
    filename  = "index.py"
  }
}


resource "aws_lambda_function" "lambda" {
  function_name           = var.name
  description             = var.description
  role                    = aws_iam_role.execution_role.arn
  runtime                 = "python3.9"
  filename                = data.archive_file.deployment_bundle.output_path
  handler                 = "index.${var.handler_function}"
  memory_size             = var.memory_size
  timeout                 = var.timeout

  dynamic "environment" {
    for_each              = (length(var.envars) > 0) ? toset(["1"]) : toset([])
    content {
      variables           = var.envars
    }
  }
}


resource "aws_iam_role" "execution_role" {
  name                = "${var.name}-ExecutionRole-${local.aws_region}"
  path                = "/lambda/"

  assume_role_policy  = jsonencode({
                          Version   = "2012-10-17"
                          Statement = [{
                            Principal = { "Service": "lambda.amazonaws.com" },
                            Effect    = "Allow",
                            Action    = "sts:AssumeRole"
                          }]
                        })

  managed_policy_arns = [
                          "arn:aws:iam::aws:policy/AWSXRayDaemonWriteAccess"
                        ]
  inline_policy {
      name          = "OperationalPermissions"
      policy        = jsonencode({
                        Version   = "2012-10-17"
                        Statement = concat(var.policy_statements,
                                    [{
                                      Sid       = "Logging",
                                      Effect    = "Allow",
                                      Action    = [
                                                    "logs:CreateLogStream",
                                                    "logs:PutLogEvents",
                                                  ],
                                      Resource  = "${aws_cloudwatch_log_group.log_group.arn}:*"
                                    }])
                      })
  }
}


resource "aws_cloudwatch_log_group" "log_group" {
  name              = "/aws/lambda/${var.name}"
  retention_in_days = 30
}
