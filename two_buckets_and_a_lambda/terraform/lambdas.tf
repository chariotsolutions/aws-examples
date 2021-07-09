# Declare things common to some/all of the lambdas.

# xxkdg Two reasons to eliminate this local:
#
# 1) It's used once.  (I don't think it would make sense to use it again,
# because then two roles would share a name.)  Defining something to use
# once is verbose and doesn't add to DRYness.
#
# <RANT>
# 2) It's a name for a name.  I think that (dedicated) names for names
# are usually a waste.  There is a fruit in my kitchen.  The name in
# English is "banana".  The name for the name is also "banana".  How
# weird and confusing would it be if the name for that word were something
# other than the quoted word itself?  The only exception I can think of
# is the Tetragrammaton, and boy is that different.
# </RANT>
locals {
    execution_role_name = "${var.base_lambda_name}-lambda-exec-role-${local.aws_region}"
}

# xxkdg  I made this common between the lambdas.  Should it be?
resource "aws_iam_role" "lambda_execution_role" {
  name               = local.execution_role_name
  path               = "/lambda/"
  assume_role_policy = data.aws_iam_policy_document.lambda_trust_policy.json
  managed_policy_arns = [
    "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
    "arn:aws:iam::aws:policy/AWSXRayDaemonWriteAccess"           # xxx needed only for c
  ]
}

# xxkdg  Ditto.
data "aws_iam_policy_document" "lambda_trust_policy" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type          = "Service"
      identifiers   = ["lambda.amazonaws.com"]
    }
  }
}

# xxx needed only for c
data aws_iam_policy_document role_trust_policy {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
        type      = "AWS"
        identifiers = [aws_iam_role.lambda_execution_role.arn]
    }
  }
} 

# xxx needed only for c
resource aws_iam_role credentials-assumed-role {
  # xxx This is too broad.  It allows any lambda to assume it.  Should just be credentials lambda
  # , which will require a new policy document.
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

