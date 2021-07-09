# Declares the lambda for credentials.js.

# xxkdg I did a separate ZIP for each of the two py files.  Shall I use
# just one ZIP?
data "archive_file" "credentials-archive" {
    type        = "zip"
    source_file = "${path.module}/lambdas/credentials-lambda.py"
    output_path = "${path.module}/credentials-archive.zip"
}

resource aws_lambda_function credentials-lambda {
    function_name = "${var.base_lambda_name}-credentials-lambda-function"
    role          = aws_iam_role.lambda_execution_role.arn
    runtime       = "python3.7"
    handler            = "credentials-lambda.lambda_handler"
    filename      = "./credentials-archive.zip"
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
        identifiers = [aws_iam_role.lambda_execution_role.arn]
    }
  }
} 

resource aws_iam_role credentials-assumed-role {
  # xxkdg Is the following line too broad?  It allows any lambda to assume 
  # it.  Should it just allow the credentials lambda (which would require
  # a new policy document)?
  assume_role_policy = data.aws_iam_policy_document.role_trust_policy.json
  managed_policy_arns = [aws_iam_policy.base_upload_policy.arn]
}

resource "aws_iam_policy" "base_upload_policy" {
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "s3:PutObject*",
        ]
        Effect   = "Allow"
        Resource = [aws_s3_bucket.upload_bucket.arn]
      },
    ]
  })
}

