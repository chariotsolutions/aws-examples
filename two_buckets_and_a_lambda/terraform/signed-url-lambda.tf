# Declares the lambda for signed-url.js.

locals {
    execution_role_name = "${var.signed_url_lambda_name}-execution_role-${local.aws_region}"
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

data "archive_file" "signed-url-archive" {
    type        = "zip"
    source_file = "lambdas/signed-url-lambda.py"
    output_path = "./signed-url-archive.zip"
}

resource "aws_iam_role" "lambda_execution_role" {
  name               = local.execution_role_name
  path               = "/lambda/"
  assume_role_policy = data.aws_iam_policy_document.lambda_trust_policy.json
}

resource aws_lambda_function signed-url-lambda {
    function_name = "signed-url-lambda-function"
    role          = aws_iam_role.lambda_execution_role.arn
    runtime       = "python3.7"
    handler            = var.signed_url_lambda_entry_point
    filename      = "./signed-url-archive.zip"
}
