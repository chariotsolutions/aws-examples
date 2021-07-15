# Declare things common to some/all of the lambdas.

# xxkdg  I made this common between the lambdas.  Should it be?  Specifically,
# the AWSXRayDaemonWriteAccess is needed only by the credentials lambda,
# not the signed-url lambda.  So the principle of least privilege says to
# split, but the "write fewer lines of code" principle (?!) says not to.
#
# xxkdg   What I wrote above about adding credentials lambda is even more
# an issue now with processing-lambda.  Split into 3?
resource aws_iam_role lambda_execution_role {
  name               = "${var.base_lambda_name}-lambda-exec-role-${local.aws_region}"
  path               = "/lambda/"
  assume_role_policy = data.aws_iam_policy_document.lambda_trust_policy.json
}

# xxkdg  Ditto for these attachments.  I believe that splitting
# this one would go along with splitting the above.
 # xxx not #s
resource aws_iam_role_policy_attachment lambda_execution_role_upload_attachment_awslambdabasicexecutionrole {
    role = aws_iam_role.lambda_execution_role.name
    policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource aws_iam_role_policy_attachment lambda_execution_role_upload_attachmentawsxraydaemonwriteaccess {
    role = aws_iam_role.lambda_execution_role.name
    policy_arn = "arn:aws:iam::aws:policy/AWSXRayDaemonWriteAccess"
}

resource aws_iam_role_policy_attachment lambda_execution_role_upload_attachmentupload {
    role = aws_iam_role.lambda_execution_role.name
    policy_arn = aws_iam_policy.read_from_upload_policy.arn
}

# xxkdg  Ditto.  I believe that splitting this one would go along with
# splitting the above.
data aws_iam_policy_document lambda_trust_policy {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type          = "Service"
      identifiers   = ["lambda.amazonaws.com"]
    }
  }
}

resource aws_iam_policy read_from_upload_policy {
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

