# Declares the lambda for signed-url.js.

locals {
    execution_role_name = "${var.base_lambda_name}-signed-url-lambda-exec-role-${local.aws_region}"
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
    source_file = "${path.module}/lambdas/signed-url-lambda.py"
    output_path = "${path.module}/signed-url-archive.zip"
}

resource "aws_iam_role" "lambda_execution_role" {
  name               = local.execution_role_name
  path               = "/lambda/"
  assume_role_policy = data.aws_iam_policy_document.lambda_trust_policy.json
  managed_policy_arns = ["arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"]
}

resource aws_lambda_function signed-url-lambda {
    function_name = "${var.base_lambda_name}-signed-url-lambda-function"
    role          = aws_iam_role.lambda_execution_role.arn
    runtime       = "python3.7"
    handler            = "signed-url-lambda.lambda_handler"
    filename      = "./signed-url-archive.zip"
    environment {
        variables = {
            UPLOAD_BUCKET = local.upload_bucket_name
        }
    }
}
