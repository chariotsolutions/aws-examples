variable "lambda_name" {
    description = "The name for the Lambda itself; also used for dependent resources"
    type        = string
    default     = "ContainerExample"
}

variable "image_name" {
    description = "The name of the Lambda's image in ECR"
    type        = string
    default     = "container-example"
}

variable "image_tag" {
    description = "The version of the image to load"
    type        = string
    default     = "latest"
}

