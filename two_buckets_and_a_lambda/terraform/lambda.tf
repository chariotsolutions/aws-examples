resource aws_iam_policy upload_policy {
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

