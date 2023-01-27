##
## Creates and configures all buckets
##
## The "static" and "archive" buckets are simple. The "upload" bucket, which involves
## user interaction, requires more configuration.
##
## I also populate the static content here. Definitely not recommended as a production
## practice, but we only have a few files. They're defined as an array of maps, and
## iterated using count; if you add files to an existing deployment, add them to the
## end of the list.
##

locals {
  static_files = {
                 "index.html"         = "text/html; charset=utf-8"
                 "js/credentials.js"  = "text/javascript"
                 "js/signed-url.js"   = "text/javascript"
                 }
}


resource "aws_s3_bucket" "static" {
  bucket            = "${var.base_bucket_name}-static"
  force_destroy     = true
}

resource "aws_s3_bucket_acl" "static" {
  bucket            = aws_s3_bucket.static.id
  acl               = "public-read"
}

resource "aws_s3_bucket_public_access_block" "static" {
  bucket = aws_s3_bucket.static.id
  block_public_acls       = false
  block_public_policy     = true
  ignore_public_acls      = false
  restrict_public_buckets = true
}

resource "aws_s3_object" "static" {
  for_each          = local.static_files
  bucket            = aws_s3_bucket.static.id
  key               = each.key
  source            = "${path.root}/../static/${each.key}"
  content_type      = each.value
  acl               = "public-read"
}


resource "aws_s3_bucket" "upload" {
  bucket            = "${var.base_bucket_name}-upload"
  force_destroy     = true
}

resource "aws_s3_bucket_cors_configuration" "upload" {
  bucket            = aws_s3_bucket.upload.id
  cors_rule {
    allowed_methods = ["PUT", "POST"]
    allowed_origins = ["*"]
    allowed_headers = ["*"]
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "upload" {
  bucket            = aws_s3_bucket.upload.id

  rule {
    id              = "DeleteIncompleteMultipartUploads"
    status          = "Enabled"
    abort_incomplete_multipart_upload {
      days_after_initiation = 1
    }
  }
}

resource "aws_s3_bucket_notification" "bucket_notification" {
  depends_on            = [ aws_lambda_permission.processing_lambda ]
  bucket                = aws_s3_bucket.upload.id
  lambda_function {
    lambda_function_arn = module.processing_lambda.lambda.arn
    events              = [ "s3:ObjectCreated:*" ]
  }

}


resource "aws_s3_bucket" "archive" {
  bucket            = "${var.base_bucket_name}-archive"
  force_destroy     = true
}
