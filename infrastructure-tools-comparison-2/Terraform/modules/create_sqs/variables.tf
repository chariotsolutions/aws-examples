variable "queue_name" {
  description = "The name of the queue. Used as a prefix for related resource names."
  type = string
}


variable "retention_period" {
  description = "Time (in seconds) that messages will remain in queue before being purged"
  type = number
  default = 86400
}


variable "visibility_timeout" {
  description = "Time (in seconds) that messages will be unavailable after being read"
  type = number
  default = 60
}


variable "retry_count" {
  description = "The number of times that a message will be delivered before being moved to dead-letter queue"
  type = number
  default = 3
}
