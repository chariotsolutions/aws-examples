provider "aws" {}


resource "aws_ecr_repository" "lambda_container" {
  name                 = var.image_name
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}


resource "aws_ecr_repository_policy" "lambda_container_policy" {
  repository = aws_ecr_repository.lambda_container.name
  policy = data.aws_iam_policy_document.lambda_container_policy.json
}


data "aws_iam_policy_document" "lambda_container_policy" {
  statement {
    sid           = "AllowLambda"
    effect        = "Allow"
    principals    {
      type        = "Service"
      identifiers = [ "lambda.amazonaws.com" ]
    }
    actions       = [
                      "ecr:BatchGetImage",
                      "ecr:DeleteRepositoryPolicy",
                      "ecr:GetDownloadUrlForLayer",
                      "ecr:GetRepositoryPolicy",
                      "ecr:SetRepositoryPolicy"
                    ]
  }
}
