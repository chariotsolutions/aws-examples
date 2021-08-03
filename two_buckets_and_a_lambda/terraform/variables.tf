variable api_gateway_name {
    description = "The name for the API Gateway"
    type        = string
    default     = "two_buckets_and_a_lambda"
}

variable bucket_name_base {
    description = "All the bucket names will start with this"
    type = string
}

