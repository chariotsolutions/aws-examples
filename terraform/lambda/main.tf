provider "aws" {}

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

locals {
    aws_account_id = data.aws_caller_identity.current.account_id
    aws_region     = data.aws_region.current.name
}

# CloudWatch Log Group

resource "aws_cloudwatch_log_group" "lambda_log_group" {
  name              = "/aws/lambda/${var.lambda_name}"
  retention_in_days = 3
}

# Execution Role

resource "aws_iam_role" "lambda_execution_role" {
  name               = "${var.lambda_name}-${local.aws_region}-ExecutionRole"
  path               = "/lambda/"
  assume_role_policy = data.aws_iam_policy_document.lambda_trust_policy.json
}

resource "aws_iam_role_policy_attachment" "lambda_execution_role_attach-1" {
  role       = aws_iam_role.lambda_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

data "aws_iam_policy_document" "lambda_trust_policy" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type          = "Service"
      identifiers   = ["lambda.amazonaws.com"]
    }
  }
}

# The Lambda itself

resource "aws_lambda_function" "lambda" {
  function_name     = var.lambda_name
  description       = "Lambda function that uses a container image"

  package_type      = "Image"
  image_uri         = "${local.aws_account_id}.dkr.ecr.${local.aws_region}.amazonaws.com/${var.image_name}:${var.image_tag}"

  role              = aws_iam_role.lambda_execution_role.arn

  memory_size       = 256
  timeout           = 15
}
