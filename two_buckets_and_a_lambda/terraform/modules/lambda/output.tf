output "lambda" {
  description = "The Lambda function"
  value       = aws_lambda_function.lambda
}


output "execution_role" {
  description = "The Lambda's execution role"
  value       = aws_iam_role.execution_role
}
