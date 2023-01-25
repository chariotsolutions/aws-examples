variable "base_name" {
  description     = "Name used for most of the resources in this stack"
  type            = string
  default         = "TwoBuckets"
}


variable "base_bucket_name" {
  description     = "The name used as a prefix for all buckets created by this stack"
  type            = string
}
