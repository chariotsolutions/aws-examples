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


