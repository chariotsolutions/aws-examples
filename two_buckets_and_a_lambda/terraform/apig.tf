# Declares the API Gateways.

resource aws_apigatewayv2_api api {
    # xxx Is this a good name?
    name = "agate"
    protocol_type = "HTTP"
}

resource aws_apigatewayv2_integration main_page {
    api_id                 = aws_apigatewayv2_api.api.id
    integration_type       = "HTTP_PROXY"
    integration_method     = "GET"
    # xxx The following should not be hard-coded, but should use interpolation of variables
    integration_uri        = "https://com-chariotsolutions-emortontf-static.s3.${var.aws_region}.amazonaws.com/index.html"
}

resource aws_apigatewayv2_integration js {
    api_id                 = aws_apigatewayv2_api.api.id
    integration_type       = "HTTP_PROXY"
    integration_method     = "GET"
    # xxx The following should not be hard-coded, but should use interpolation of variables
    integration_uri        = "https://com-chariotsolutions-emortontf-static.s3.${var.aws_region}.amazonaws.com/js/{name}"
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

  # More: http://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-control-access-using-iam-policies-to-invoke-api.html
  # xxx Should the POST be replaced by an interpolated reference?
  # xxx add the source_arn back in
  #  source_arn = "arn:aws:execute-api:${var.myregion}:${var.accountId}:${aws_apigatewayv2_api.api.id}/*/POST${aws_api_gateway_resource.resource.path}"
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

resource aws_apigatewayv2_stage api_stage_default {
    api_id = aws_apigatewayv2_api.api.id
    name = "$default"
    auto_deploy = true
    access_log_settings {
        destination_arn = "arn:aws:logs:${var.aws_region}:567196586496:log-group:api-gateway"
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
              messageString  = "$context.error.messageString"
            })
    }
}

