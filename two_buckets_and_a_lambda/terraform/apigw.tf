##
## Creates the API Gateway and links it to the Lambdas
##

resource "aws_apigatewayv2_api" "main" {
  name                  = var.base_name
  description           = "Two Buckets and a Lambda Web-App"
  protocol_type         = "HTTP"
}


resource "aws_apigatewayv2_route" "root" {
  api_id                = aws_apigatewayv2_api.main.id
  route_key             = "GET /"
  target                = "integrations/${aws_apigatewayv2_integration.root.id}"
}

resource "aws_apigatewayv2_integration" "root" {
  api_id                = aws_apigatewayv2_api.main.id
  integration_type      = "HTTP_PROXY"
  integration_method    = "GET"
  integration_uri       = "https://${aws_s3_bucket.static.bucket_domain_name}/index.html"
}


resource "aws_apigatewayv2_route" "static" {
  api_id                = aws_apigatewayv2_api.main.id
  route_key             = "GET /{proxy+}"
  target                = "integrations/${aws_apigatewayv2_integration.static.id}"
}

resource "aws_apigatewayv2_integration" "static" {
  api_id                = aws_apigatewayv2_api.main.id
  integration_type      = "HTTP_PROXY"
  integration_method    = "GET"
  integration_uri       = "https://${aws_s3_bucket.static.bucket_domain_name}/{proxy}"
}


resource "aws_apigatewayv2_route" "credentials" {
  api_id                = aws_apigatewayv2_api.main.id
  route_key             = "POST /api/credentials"
  target                = "integrations/${aws_apigatewayv2_integration.credentials.id}"
}

resource "aws_apigatewayv2_integration" "credentials" {
  api_id                = aws_apigatewayv2_api.main.id
  integration_type      = "AWS_PROXY"
  integration_method    = "POST"
  integration_uri       = module.credentials_lambda.lambda.invoke_arn
}


resource "aws_apigatewayv2_route" "signed_url" {
  api_id                = aws_apigatewayv2_api.main.id
  route_key             = "POST /api/signedurl"
  target                = "integrations/${aws_apigatewayv2_integration.signed_url.id}"
}

resource "aws_apigatewayv2_integration" "signed_url" {
  api_id                = aws_apigatewayv2_api.main.id
  integration_type      = "AWS_PROXY"
  integration_method    = "POST"
  integration_uri       = module.signed_url_lambda.lambda.invoke_arn
}


resource "aws_apigatewayv2_stage" "main" {
  api_id                = aws_apigatewayv2_api.main.id
  name                  = "$default"
  description           = "Default auto-deployed stage"
  auto_deploy           = true
  access_log_settings {
    destination_arn     = aws_cloudwatch_log_group.apigw.arn
    format              = jsonencode({
                            "requestId":                  "$context.requestId",
                            "ip":                         "$context.identity.sourceIp",
                            "requestTime":                "$context.requestTime",
                            "httpMethod":                 "$context.httpMethod",
                            "path":                       "$context.path",
                            "routeKey":                   "$context.routeKey",
                            "status":                     "$context.status",
                            "protocol":                   "$context.protocol",
                            "responseLength":             "$context.responseLength",
                            "context.integration.error":  "$context.integration.error",
                            "context.integration.status": "$context.integration.status"
                          })
  }
}


resource "aws_cloudwatch_log_group" "apigw" {
  name              = "/apigateway/${var.base_name}"
  retention_in_days = 30
}
