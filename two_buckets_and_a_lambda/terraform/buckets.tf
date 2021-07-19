## Declares all the buckets.

locals {
    upload_bucket_name  = "${local.bucket_name_base}-uploads"
    static_bucket_name  = "${local.bucket_name_base}-static"
    archive_bucket_name = "${local.bucket_name_base}-archive"
}

resource aws_s3_bucket upload_bucket {
  bucket = local.upload_bucket_name
  acl    = "public-read"

  cors_rule {
         allowed_headers = [ "*", ]
         allowed_methods = [ "PUT", "POST", ]
         allowed_origins = [ "*", ]
         expose_headers  = [ "ETag", ]
         max_age_seconds = 0
  }
}

resource aws_s3_bucket archive_bucket {
  bucket = local.archive_bucket_name
  acl    = "private"

}

resource aws_s3_bucket static_bucket {
  bucket = local.static_bucket_name
  acl    = "private"

}

resource aws_s3_bucket_object whatever_static_item {
  for_each = {
      "index.html" = "text/html; charset=utf-8"
      "favicon.ico" = "image/x-icon"
      "js/credentials.js" = "text/javascript"
      "js/signed-url.js" = "text/javascript"
  }
  bucket = aws_s3_bucket.static_bucket.id
  key = each.key
  source = "${path.module}/../static/${each.key}"
  acl    = "public-read"
  content_type = each.value
  etag = filemd5("${path.module}/../static/${each.key}")
}

