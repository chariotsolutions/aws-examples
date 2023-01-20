# Declares the lambda that does the "processing," which
# consists of moving the file.

data archive_file processing_archive {
    type        = "zip"
    source_file = "${path.module}/lambdas/processing-lambda.py"
    output_path = "${path.module}/processing_archive.zip"
}

resource aws_lambda_function processing_lambda {
    function_name = "${var.name_base}_processing"
    role          = aws_iam_role.processing_lambda_execution_role.arn
    runtime       = "python3.9"
    handler       = "processing-lambda.lambda_handler"
    filename      = "./processing_archive.zip"
    source_code_hash  = "${data.archive_file.processing_archive.output_base64sha256}"
    environment {
        variables = {
            # Requires only the archive bucket name.  The upload
            # bucket name gets passed to it when triggered.
            ARCHIVE_BUCKET = local.archive_bucket_name
        }
    }
}

resource aws_cloudwatch_log_group processing_log_group {
    name              = "/aws/lambda/${aws_lambda_function.processing_lambda.function_name}"
    retention_in_days = 7
}

resource aws_lambda_permission upload_bucket_lambda_invocation {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.processing_lambda.arn
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.upload_bucket.arn
}

resource aws_s3_bucket_notification upload_bucket_notification {
  bucket = aws_s3_bucket.upload_bucket.id
  lambda_function {
    lambda_function_arn = aws_lambda_function.processing_lambda.arn
    events              = ["s3:ObjectCreated:*"]
  }

  depends_on = [aws_lambda_permission.upload_bucket_lambda_invocation]
}

resource aws_iam_role processing_lambda_execution_role {
  name               = "${var.name_base}-Processing-ExecutionRole-${local.aws_region}"
  path               = "/lambda/"
  assume_role_policy = data.aws_iam_policy_document.processing_exec_role_lambda_trust_policy.json
  inline_policy {
    # Change to match CloudFormation.
    name = "anameisrequired"
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
}

resource aws_iam_role_policy_attachment processing_lambda_write {
    role = aws_iam_role.processing_lambda_execution_role.name
    policy_arn = "arn:aws:iam::aws:policy/AWSXRayDaemonWriteAccess"
}

resource aws_iam_role_policy_attachment processing_basic_lambda {
    role = aws_iam_role.processing_lambda_execution_role.name
    policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

data aws_iam_policy_document processing_exec_role_lambda_trust_policy {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type          = "Service"
      identifiers   = ["lambda.amazonaws.com"]
    }
  }
}

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


