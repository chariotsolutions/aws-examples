package com.chariotsolutions.example;

import com.amazonaws.services.securitytoken.AWSSecurityTokenService;
import com.amazonaws.services.securitytoken.AWSSecurityTokenServiceClientBuilder;
import com.amazonaws.services.securitytoken.model.*;


/**
 *  Retrieves the caller's identity using a default client.
 */
public class NoProxy
{
    public static void main(String[] argv)
    throws Exception
    {
        AWSSecurityTokenService client = AWSSecurityTokenServiceClientBuilder.defaultClient();

        GetCallerIdentityRequest request = new GetCallerIdentityRequest();
        GetCallerIdentityResult response = client.getCallerIdentity(request);

        System.out.println("account: " + response.getAccount());
        System.out.println("user id: " + response.getUserId());
        System.out.println("arn:     " + response.getArn());
    }
}
