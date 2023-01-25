variable "name" {
  description = "The name of the Lambda; also used as the base name for its execution role"
  type        = string
}

variable "description" {
  description = "Describes the Lambda's purpose"
  type        = string
}

variable "source_file" {
  description = "Path to the single-module file containing the Lambda source code"
  type        = string
}

variable "envars" {
  description = "A map of environment variables"
  type        = map(string)
  default     = {}
}

variable "policy_statements" {
  description = "Policy statements that are added to the Lambda's execution role"
  type        = list(any)
}

## the variables defined below this point are intended as constants

variable "handler_function" {
  description = "The simple name of the Lambda's handler function (will be combined with standard module name)"
  type        = string
  default     = "lambda_handler"
}

variable "memory_size" {
  description = "Amount of memory given to Lambda execution environment"
  type        = number
  default     = 512
}

variable "timeout" {
  description = "number of seconds that the Lambda is allowed to run"
  type        = number
  default     = 10
}
