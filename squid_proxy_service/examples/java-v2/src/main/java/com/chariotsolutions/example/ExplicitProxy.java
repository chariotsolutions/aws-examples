package com.chariotsolutions.example;


import java.net.URI;

import software.amazon.awssdk.http.apache.ApacheHttpClient;
import software.amazon.awssdk.http.apache.ProxyConfiguration;
import software.amazon.awssdk.services.sts.StsClient;
import software.amazon.awssdk.services.sts.model.*;

/**
 *  Retrieves the caller's identity using an explicit proxy server with the Apache HTTP client.
 *  Other clients have similar features.
 */
public class ExplicitProxy
{
    public static void main(String[] argv)
    throws Exception
    {
        ProxyConfiguration config = ProxyConfiguration.builder()
                                    .endpoint(new URI("http://squid_proxy.internal:3128"))
                                    .addNonProxyHost("169.254.169.254")
                                    .useSystemPropertyValues(Boolean.FALSE)
                                    .build();

        ApacheHttpClient.Builder clientBuilder = ApacheHttpClient.builder()
                                                 .proxyConfiguration(config);

        StsClient client = StsClient.builder()
                           .httpClientBuilder(clientBuilder)
                           .build();

        GetCallerIdentityRequest request = GetCallerIdentityRequest.builder().build();
        GetCallerIdentityResponse response = client.getCallerIdentity(request);

        System.out.println("account: " + response.account());
        System.out.println("user id: " + response.userId());
        System.out.println("arn:     " + response.arn());
    }

}
