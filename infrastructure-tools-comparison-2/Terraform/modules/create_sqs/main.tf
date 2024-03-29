##
## A module that creates an SQS queue, along with a related dead-letter queue,
## and policies to read/write both
##

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 4.0.0"
    }
  }
}

data "aws_region" "current" {}


resource "aws_sqs_queue" "base_queue" {
  name                        = var.queue_name
  message_retention_seconds   = var.retention_period
  visibility_timeout_seconds  = var.visibility_timeout
  redrive_policy              = jsonencode({
                                    "deadLetterTargetArn" = aws_sqs_queue.deadletter_queue.arn,
                                    "maxReceiveCount" = var.retry_count
                                })
}


resource "aws_sqs_queue" "deadletter_queue" {
  name                        = "${var.queue_name}-DLQ"
  message_retention_seconds   = var.retention_period
  visibility_timeout_seconds  = var.visibility_timeout
}


resource "aws_iam_policy" "consumer_policy" {
  name        = "SQS-${var.queue_name}-${data.aws_region.current.name}-Consumer"
  description = "Attach this policy to consumers of SQS queue ${var.queue_name}"
  policy      = data.aws_iam_policy_document.consumer_policy.json
}


data "aws_iam_policy_document" "consumer_policy" {
  statement {
    actions = [
      "sqs:ChangeMessageVisibility",
      "sqs:ChangeMessageVisibilityBatch",
      "sqs:DeleteMessage",
      "sqs:DeleteMessageBatch",
      "sqs:GetQueueAttributes",
      "sqs:GetQueueUrl",
      "sqs:ReceiveMessage"
    ]
    resources = [
      aws_sqs_queue.base_queue.arn,
      aws_sqs_queue.deadletter_queue.arn
    ]
  }
}


resource "aws_iam_policy" "producer_policy" {
  name        = "SQS-${var.queue_name}-${data.aws_region.current.name}-Producer"
  description = "Attach this policy to producers for SQS queue ${var.queue_name}"
  policy      = data.aws_iam_policy_document.producer_policy.json
}


data "aws_iam_policy_document" "producer_policy" {
  statement {
    actions = [
      "sqs:GetQueueAttributes",
      "sqs:GetQueueUrl",
      "sqs:SendMessage",
      "sqs:SendMessageBatch"
    ]
    resources = [
      aws_sqs_queue.base_queue.arn
    ]
  }
}
