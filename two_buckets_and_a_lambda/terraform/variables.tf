variable "base_lambda_name" {
    description = "The base for names of lambdas"
    type        = string
    default     = "two_buckets_and_a_lambda"
}

variable "api_gateway_name" {
    description = "The name for the API Gateway"
    type        = string
    default     = "agate"
}

