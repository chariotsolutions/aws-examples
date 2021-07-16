# Declares the lambda that does the "processing," which
# consists of moving the file.

data archive_file processing-archive {
    type        = "zip"
    source_file = "${path.module}/lambdas/processing-lambda.py"
    output_path = "${path.module}/processing-archive.zip"
}

resource aws_lambda_function processing-lambda {
    function_name = "${var.base_lambda_name}-processing-lambda-function"
    role          = aws_iam_role.processing_lambda_execution_role.arn
    runtime       = "python3.7"
    handler            = "processing-lambda.lambda_handler"
    filename      = "./processing-archive.zip"
    source_code_hash  = "${data.archive_file.processing-archive.output_base64sha256}"
    environment {
        variables = {
            # Requires only the archive bucket name.  The upload
            # bucket name gets passed to it when triggered.
            ARCHIVE_BUCKET = local.archive_bucket_name
        }
    }
}

resource aws_lambda_permission allow_upload_bucket {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.processing-lambda.arn
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.upload_bucket.arn
}

resource aws_s3_bucket_notification upload_bucket_notification {
  bucket = aws_s3_bucket.upload_bucket.id
  lambda_function {
    lambda_function_arn = aws_lambda_function.processing-lambda.arn
    events              = ["s3:ObjectCreated:*"]
  }

  depends_on = [aws_lambda_permission.allow_upload_bucket]
}

resource aws_iam_role processing_lambda_execution_role {
  name               = "${var.base_lambda_name}-processing-lambda-exec-role-${local.aws_region}"
  path               = "/lambda/"
  assume_role_policy = data.aws_iam_policy_document.processing_lambda_trust_policy.json
}

#resource aws_iam_role_policy_attachment processing_lambda_execution_role_upload_attachment_awslambdabasicexecutionrole {
#    role = aws_iam_role.processing_lambda_execution_role.name
#    policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
#}

resource aws_iam_role_policy_attachment processing_lambda_execution_role_upload_attachmentawsxraydaemonwriteaccess {
    role = aws_iam_role.processing_lambda_execution_role.name
    policy_arn = "arn:aws:iam::aws:policy/AWSXRayDaemonWriteAccess"
}

resource aws_iam_role_policy_attachment processing_lambda_execution_role_upload_attachmentupload {
    role = aws_iam_role.processing_lambda_execution_role.name
    policy_arn = aws_iam_policy.process_read_from_upload_policy.arn
}

data aws_iam_policy_document processing_lambda_trust_policy {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type          = "Service"
      identifiers   = ["lambda.amazonaws.com"]
    }
  }
}

#resource aws_iam_policy processing_lambda_read_from_upload_policy {
#  policy = jsonencode({
#    Version = "2012-10-17"
#    Statement = [
#      {
#        Action = [
#          "s3:GetObject",
#          "s3:DeleteObject",
#        ]
#        Effect   = "Allow"
#        Resource = ["${aws_s3_bucket.upload_bucket.arn}/*"]
#      },
#      {
#        Action = [
#          "s3:PutObject",
#        ]
#        Effect   = "Allow"
#        Resource = ["${aws_s3_bucket.archive_bucket.arn}/*"]
#      },
#    ]
#  })
#}

resource aws_iam_policy process_read_from_upload_policy {
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "s3:GetObject",
          "s3:DeleteObject",
        ]
        Effect   = "Allow"
        Resource = ["${aws_s3_bucket.upload_bucket.arn}/*"]
      },
      {
        Action = [
          "s3:PutObject",
        ]
        Effect   = "Allow"
        Resource = ["${aws_s3_bucket.archive_bucket.arn}/*"]
      },
    ]
  })
}


