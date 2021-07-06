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

resource "aws_s3_bucket_object" "whatever_static_item" {
  # xxkdg
  # You said to use a "for_each that's driven by a map defined as a local."
  # I used a for_each, but deviated from your suggestion in two ways.
  #
  # 1) I used a set of strings, rather than a map, at least as those two terms
  # are used on https://www.terraform.io/docs/language/meta-arguments/for_each.html .
  # It seems like the map would be overkill, because it gives key and value, and we
  # need only one of those.
  # 2) I put the set of strings inside the resource definition, rather than making
  # it a variable.  That's because the variable would make sense in only one place.
  #
  # Are those changes OK?
  #
  for_each = toset(["index.html","js/credentials.js","js/signed-url.js"])
  bucket = aws_s3_bucket.static_bucket.id
  key = each.key
  source = "${path.module}/../static/${each.key}"
  acl    = "public-read"
  content_type = "text/html; charset=utf-8"
  etag = filemd5("${path.module}/../static/${each.key}")
}

