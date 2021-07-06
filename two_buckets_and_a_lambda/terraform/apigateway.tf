# Declares the API Gateways.

resource aws_apigatewayv2_api api {
    name = "agate"
    protocol_type = "HTTP"
}

resource aws_apigatewayv2_integration main_page {
    api_id                 = aws_apigatewayv2_api.api.id
    integration_type       = "HTTP_PROXY"
    integration_method     = "GET"
    integration_uri        = "https://${aws_s3_bucket.static_bucket.bucket_regional_domain_name}/index.html"
}

resource aws_apigatewayv2_integration js {
    api_id                 = aws_apigatewayv2_api.api.id
    integration_type       = "HTTP_PROXY"
    integration_method     = "GET"
    integration_uri        = "https://${aws_s3_bucket.static_bucket.bucket_regional_domain_name}/js/{name}"
}

resource aws_apigatewayv2_integration signed_url_lambda {
    api_id                 = aws_apigatewayv2_api.api.id
    integration_type       = "AWS_PROXY"
    integration_method     = "POST"
    integration_uri        = aws_lambda_function.signed-url-lambda.invoke_arn
}

resource "aws_lambda_permission" "api_signed_url_lambda" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.signed-url-lambda.function_name
  principal     = "apigateway.amazonaws.com"

  source_arn = "${aws_apigatewayv2_api.api.execution_arn}/*/*/*"
}

resource aws_apigatewayv2_route main_page {
    api_id    = aws_apigatewayv2_api.api.id
    route_key = "GET /"
    target    = "integrations/${aws_apigatewayv2_integration.main_page.id}"
}

resource aws_apigatewayv2_route js {
    api_id    = aws_apigatewayv2_api.api.id
    route_key = "GET /js/{name}"
    target    = "integrations/${aws_apigatewayv2_integration.js.id}"
}

resource aws_apigatewayv2_route signed_url_lambda {
    api_id    = aws_apigatewayv2_api.api.id
    route_key = "POST /api/signedurl"
    target    = "integrations/${aws_apigatewayv2_integration.signed_url_lambda.id}"
}

resource aws_cloudwatch_log_group log_group {
    name = "two_buckets_and_a_lambda_log_group"
    retention_in_days = 5
}

resource aws_apigatewayv2_stage api_stage_default {
    api_id = aws_apigatewayv2_api.api.id
    name = "$default"
    auto_deploy = true
    access_log_settings {
        destination_arn = aws_cloudwatch_log_group.log_group.arn
        format          = jsonencode(
            {
              status         = "$context.status",
              httpMethod     = "$context.httpMethod",
              ip             = "$context.identity.sourceIp",
              protocol       = "$context.protocol",
              requestId      = "$context.requestId",
              requestTime    = "$context.requestTime",
              responseLength = "$context.responseLength",
              routeKey       = "$context.routeKey",
              integration_error_status = "$context.integrationStatus",
              integration_error_message = "$context.integrationErrorMessage",
              message        = "$context.error.message",
              messageString  = "$context.error.messageString",
              context_path   = "$context.path"
            })
    }
}

output "url-for-index-page" {
  value = aws_apigatewayv2_api.api.api_endpoint
}
