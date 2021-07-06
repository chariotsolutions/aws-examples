## Declares all the buckets.

locals {
    upload_bucket_name  = "${local.bucket_name_base}-uploads"
    static_bucket_name  = "${local.bucket_name_base}-static"
    archive_bucket_name = "${local.bucket_name_base}-archive"
}

resource "aws_s3_bucket" "upload_bucket" {
  bucket = local.upload_bucket_name
  acl    = "public-read-write"

  cors_rule {
         allowed_headers = [ "*", ]
         allowed_methods = [ "PUT", "POST", ]
         allowed_origins = [ "*", ]
         expose_headers  = [ "ETag", ]
         max_age_seconds = 0
  }
}

resource "aws_s3_bucket" "archive_bucket" {
  bucket = local.archive_bucket_name
  acl    = "private"

}


resource "aws_s3_bucket" "static_bucket" {
  bucket = local.static_bucket_name
  acl    = "private"

}

resource "aws_s3_bucket_object" "main_page" {
  bucket = aws_s3_bucket.static_bucket.id
  key = "index.html"
  source = "../static/index.html"
  # xxkdg For this and the other objects in the static bucket, is this acl too permissive?
  acl    = "public-read"
  content_type = "text/html; charset=utf-8"
  etag = filemd5("../static/index.html")
}
resource "aws_s3_bucket_object" "credentials_js" {
  bucket = aws_s3_bucket.static_bucket.id 
  key = "js/credentials.js"
  source = "../static/js/credentials.js"
  acl    = "public-read"
  content_type = "text/javascript"
  etag = filemd5("../static/js/credentials.js")
}
resource "aws_s3_bucket_object" "signedurl_js" {
  bucket = aws_s3_bucket.static_bucket.id 
  key = "js/signed-url.js"
  source = "../static/js/signed-url.js"
  acl    = "public-read"
  content_type = "text/javascript"
  etag = filemd5("../static/js/signed-url.js")
}

