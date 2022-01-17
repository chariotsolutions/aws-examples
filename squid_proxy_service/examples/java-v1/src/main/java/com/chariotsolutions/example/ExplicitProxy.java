package com.chariotsolutions.example;

import com.amazonaws.ClientConfiguration;
import com.amazonaws.Protocol;
import com.amazonaws.services.securitytoken.AWSSecurityTokenService;
import com.amazonaws.services.securitytoken.AWSSecurityTokenServiceClientBuilder;
import com.amazonaws.services.securitytoken.model.GetCallerIdentityRequest;
import com.amazonaws.services.securitytoken.model.GetCallerIdentityResult;


/**
 *  Retrieves the caller's identity using an explicit proxy server.
 */
public class ExplicitProxy
{
    public static void main(String[] argv)
    throws Exception
    {
        ClientConfiguration config = new ClientConfiguration()
                             .withProxyProtocol(Protocol.HTTP)
                             .withProxyHost("squid_proxy.internal")
                             .withProxyPort(3128);

        AWSSecurityTokenService client = AWSSecurityTokenServiceClientBuilder.standard()
                                         .withClientConfiguration(config)
                                         .build();

        GetCallerIdentityRequest request = new GetCallerIdentityRequest();
        GetCallerIdentityResult response = client.getCallerIdentity(request);

        System.out.println("account: " + response.getAccount());
        System.out.println("user id: " + response.getUserId());
        System.out.println("arn:     " + response.getArn());
    }
}
