# Declares the lambda for credentials.js.

data archive_file credentials-archive {
    type        = "zip"
    source_file = "${path.module}/lambdas/credentials-lambda.py"
    output_path = "${path.module}/credentials-archive.zip"
}

resource aws_lambda_function credentials-lambda {
    function_name = "${var.base_lambda_name}-credentials"
    role          = aws_iam_role.credentials_lambda_execution_role.arn
    runtime       = "python3.7"
    handler            = "credentials-lambda.lambda_handler"
    filename      = "./credentials-archive.zip"
    source_code_hash  = "${data.archive_file.credentials-archive.output_base64sha256}"
    environment {
        variables = {
            UPLOAD_BUCKET = local.upload_bucket_name
            ASSUMED_ROLE_ARN = aws_iam_role.credentials-assumed-role.arn
        }
    }
}

data aws_iam_policy_document role_trust_policy {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
        type      = "AWS"
        identifiers = [aws_iam_role.credentials_lambda_execution_role.arn]
    }
  }
} 

resource aws_iam_role credentials-assumed-role {
  assume_role_policy = data.aws_iam_policy_document.role_trust_policy.json
  managed_policy_arns = [aws_iam_policy.upload_policy.arn]
}

resource aws_iam_role credentials_lambda_execution_role {
  name               = "${var.base_lambda_name}-lambda-exec-role-${local.aws_region}"
  path               = "/lambda/"
  assume_role_policy = data.aws_iam_policy_document.credentials_lambda_trust_policy.json
}

data aws_iam_policy_document credentials_lambda_trust_policy {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type          = "Service"
      identifiers   = ["lambda.amazonaws.com"]
    }
  }
}

resource aws_lambda_permission api_credentials_lambda {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.credentials-lambda.function_name
  principal     = "apigateway.amazonaws.com"

  source_arn = "${aws_apigatewayv2_api.api.execution_arn}/*/*/*"
}

