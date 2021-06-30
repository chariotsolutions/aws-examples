## Declares all the buckets.

resource "aws_s3_bucket" "upload_bucket" {
  bucket = "${local.upload_bucket_name_base}-uploads"
  acl    = "public-read-write"

  cors_rule {
         allowed_headers = [ "*", ]
         allowed_methods = [ "PUT", "POST", ]
         allowed_origins = [ "*", ]
         expose_headers  = [ "ETag", ]
         max_age_seconds = 0
  }
#  tags = {
#    Name        = "My bucket"
#    Environment = "Dev"
#  }
}

resource "aws_s3_bucket" "archive_bucket" {
  bucket = "${local.upload_bucket_name_base}-archive"
  acl    = "private"

#  tags = {
#    Name        = "My bucket"
#    Environment = "Dev"
#  }
}


resource "aws_s3_bucket" "static_bucket" {
  bucket = "${local.upload_bucket_name_base}-static"
  acl    = "private"

#  tags = {
#    Name        = "My bucket"
#    Environment = "Dev"
#  }
}

resource "aws_s3_bucket_object" "main_page" {
  bucket = aws_s3_bucket.static_bucket.id
  key = "index.html"
  source = "../static/index.html"
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

output "utterance-from-buckets" {
#  value = data.aws_region.current.name
value = "The account id is ${data.aws_caller_identity.current.account_id}"
# value = "the region is ${local.aws_region}"
}
