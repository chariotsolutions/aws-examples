variable "signed_url_lambda_name" {
    description = "The name of the Lambda (also used for execution role)"
    type        = string
    default     = "example"
}

variable "signed_url_lambda_entry_point" {
    description = "The name of the function to invoke"
    type        = string
    default     = "index.lambda_handler"
}
