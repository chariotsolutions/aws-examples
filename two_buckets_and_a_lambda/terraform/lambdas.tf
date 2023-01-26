##
## Creates all Lambdas, using a custom module
##

module "processing_lambda" {
  source            = "./modules/lambda"

  name              = "${var.base_name}-Processor"
  description       = "Processes files uploaded to bucket ${aws_s3_bucket.upload.bucket} and moves them to bucket ${aws_s3_bucket.archive.bucket}"
  source_file       = "${path.root}/../lambda/processor.py"
  policy_statements = [
                        {
                          Sid       = "ReadFromSource",
                          Effect    = "Allow",
                          Action    = [
                                        "s3:DeleteObject",
                                        "s3:GetObject",
                                      ],
                          Resource  = "${aws_s3_bucket.upload.arn}/*"
                        },
                        {
                          Sid       = "WriteToArchive",
                          Effect    = "Allow",
                          Action    = [
                                        "s3:PutObject",
                                      ],
                          Resource  = "${aws_s3_bucket.archive.arn}/*"
                        }
                      ]
  envars            = {
                        "ARCHIVE_BUCKET": aws_s3_bucket.archive.bucket
                      }
}

resource "aws_lambda_permission" "processing_lambda" {
  action            = "lambda:InvokeFunction"
  function_name     = module.processing_lambda.lambda.arn
  principal         = "s3.amazonaws.com"
  source_account    = local.aws_account_id
  source_arn        = aws_s3_bucket.upload.arn
}


module "credentials_lambda" {
  source            = "./modules/lambda"

  name              = "${var.base_name}-Credentials"
  description       = "Generates limited-scope credentials that allow SDK uploads to bucket ${aws_s3_bucket.upload.bucket}"
  source_file       = "${path.root}/../lambda/credentials.py"
  policy_statements = [
                        {
                          Sid       = "AssumeUploadRole",
                          Effect    = "Allow",
                          Action    = [
                                        "sts:AssumeRole",
                                      ],
                          Resource  = "${aws_iam_role.credentials_assumed_role.arn}"
                        },
                      ]
  envars            = {
                        "UPLOAD_BUCKET":    aws_s3_bucket.upload.bucket,
                        "ASSUMED_ROLE_ARN": aws_iam_role.credentials_assumed_role.arn
                      }
}

resource "aws_lambda_permission" "credentials_lambda" {
  action            = "lambda:InvokeFunction"
  function_name     = module.credentials_lambda.lambda.arn
  principal         = "apigateway.amazonaws.com"
  source_arn        = "${aws_apigatewayv2_api.main.execution_arn}/*/*/*"
}


resource "aws_iam_role" "credentials_assumed_role" {
  name                = "${var.base_name}-Credentials-AssumedRole-${local.aws_region}"
  path                = "/lambda/"

  assume_role_policy  = jsonencode({
                          Version   = "2012-10-17"
                          Statement = [{
                            Principal = { "AWS": local.aws_account_id },
                            Effect    = "Allow",
                            Action    = "sts:AssumeRole"
                          }]
                        })

  inline_policy {
      name          = "BaseUploadPermissions"
      policy        = jsonencode({
                        Version   = "2012-10-17"
                        Statement = [{
                                      Sid       = "Logging",
                                      Effect    = "Allow",
                                      Action    = [
                                                    "s3:PutObject",
                                                  ],
                                      Resource  = "${aws_s3_bucket.upload.arn}/*"
                                    }]
                      })
  }
}


module "signed_url_lambda" {
  source            = "./modules/lambda"

  name              = "${var.base_name}-SignedUrl"
  description       = "Generates a signed URL that allows direct PUTs to bucket ${aws_s3_bucket.upload.bucket}"
  source_file       = "${path.root}/../lambda/signed_url.py"
  policy_statements = [
                        {
                          Sid       = "AllowUploads",
                          Effect    = "Allow",
                          Action    = [
                                        "s3:PutObject",
                                      ],
                          Resource  = "${aws_s3_bucket.upload.arn}/*"
                        },
                      ]
  envars            = {
                        "UPLOAD_BUCKET":    aws_s3_bucket.upload.bucket
                      }
}

resource "aws_lambda_permission" "signed_url_lambda" {
  action            = "lambda:InvokeFunction"
  function_name     = module.signed_url_lambda.lambda.arn
  principal         = "apigateway.amazonaws.com"
  source_arn        = "${aws_apigatewayv2_api.main.execution_arn}/*/*/*"
}
