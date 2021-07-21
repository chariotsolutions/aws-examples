# Declares the lambda for signed-url.js.

data archive_file signed-url-archive {
    type        = "zip"
    source_file = "${path.module}/lambdas/signed-url-lambda.py"
    output_path = "${path.module}/signed-url-archive.zip"
}

resource aws_lambda_function signed-url-lambda {
    function_name = "${var.base_lambda_name}-signed-url"
    role          = aws_iam_role.signed_url_lambda_execution_role.arn
    runtime       = "python3.7"
    handler            = "signed-url-lambda.lambda_handler"
    filename      = "./signed-url-archive.zip"
    source_code_hash  = "${data.archive_file.signed-url-archive.output_base64sha256}"
    environment {
        variables = {
            UPLOAD_BUCKET = local.upload_bucket_name
        }
    }
}

resource aws_iam_role signed_url_lambda_execution_role {
  name               = "${var.base_lambda_name}-signed-url-lambda-exec-role-${local.aws_region}"
  path               = "/lambda/"
  assume_role_policy = data.aws_iam_policy_document.signed_url_lambda_trust_policy.json
  inline_policy {
    # Commenting out the next line produces no error, but breaks the demo.  xxkdg any thought?
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

data aws_iam_policy_document signed_url_lambda_trust_policy {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type          = "Service"
      identifiers   = ["lambda.amazonaws.com"]
    }
  }
}

resource aws_lambda_permission api_signed_url_lambda {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.signed-url-lambda.function_name
  principal     = "apigateway.amazonaws.com"

  source_arn = "${aws_apigatewayv2_api.api.execution_arn}/*/*/*"
}

