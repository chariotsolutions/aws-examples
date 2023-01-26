output "api_gateway_url" {
  description   = "The root URL for the example"
  value         = aws_apigatewayv2_api.main.api_endpoint
}

