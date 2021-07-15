# Declares the lambda that does the "processing," which
# consists of moving the file.

data archive_file processing-archive {
    type        = "zip"
    source_file = "${path.module}/lambdas/processing-lambda.py"
    output_path = "${path.module}/processing-archive.zip"
}

resource aws_lambda_function processing-lambda {
    function_name = "${var.base_lambda_name}-processing-lambda-function"
    role          = aws_iam_role.lambda_execution_role.arn
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
