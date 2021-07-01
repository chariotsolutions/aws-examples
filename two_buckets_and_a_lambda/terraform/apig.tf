# Declares the API Gateways.

# xxx Not Fred
resource aws_apigatewayv2_api fred {
    # xxx Is this a good name?
    name = "agate"
    protocol_type = "HTTP"
}

resource aws_apigatewayv2_integration main_page {
    api_id                 = aws_apigatewayv2_api.fred.id
    integration_type       = "HTTP_PROXY"
    integration_method     = "GET"
    #xxx use for other ones, not for this one integration_uri        = aws_lambda_function.signed-url-lambda.invoke_arn
    # xxx The following should not be hard-coded, but should use interpolation of variables
    integration_uri        = "https://com-chariotsolutions-emortontf-static.s3.us-east-2.amazonaws.com/index.html"
    # payload_format_version = "2.0"
}

resource aws_apigatewayv2_route main_page {
    api_id    = aws_apigatewayv2_api.fred.id
    route_key = "GET /"
    target    = "integrations/${aws_apigatewayv2_integration.main_page.id}"
}

resource aws_apigatewayv2_stage api_stage_default {
    api_id = aws_apigatewayv2_api.fred.id
    name = "$default"
    auto_deploy = true
}

