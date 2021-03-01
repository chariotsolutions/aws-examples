output "repository_url" {
  description = "The URL (registry ID / image name) of this repository"
  value       = aws_ecr_repository.lambda_container.repository_url
}
