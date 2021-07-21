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

resource aws_iam_role credentials_lambda_execution_role {
  name               = "${var.base_lambda_name}-lambda-exec-role-${local.aws_region}"
  path               = "/lambda/"
  assume_role_policy = data.aws_iam_policy_document.credentials_exec_role_lambda_trust_policy.json
}

resource aws_iam_role_policy_attachment credentials_basic_lambda {
    role = aws_iam_role.credentials_lambda_execution_role.name
    policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

data aws_iam_policy_document credentials_exec_role_lambda_trust_policy {
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

# Data/resources for the assumed role.

data aws_iam_policy_document credentials-assumed-role-trust-policy {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
        type      = "AWS"
        identifiers = [aws_iam_role.credentials_lambda_execution_role.arn]
    }
  }
} 

resource aws_iam_role credentials-assumed-role {
  assume_role_policy = data.aws_iam_policy_document.credentials-assumed-role-trust-policy.json
  inline_policy {
    # Commenting out the next line produces no error, but breaks the demo.
    name = "anameisrequired"
    policy = jsonencode({
        Version = "2012-10-17"
        Statement = [
          {
            Action = [
              "s3:PutObject*",
            ]
            Effect   = "Allow"
            Resource = ["${aws_s3_bucket.upload_bucket.arn}/*"]
          },
        ]
      })
    }
}
