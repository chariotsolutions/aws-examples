package com.chariotsolutions.example;

import software.amazon.awssdk.services.sts.StsClient;
import software.amazon.awssdk.services.sts.model.*;

/**
 *  Retrieves the caller's identity using a default client.
 */
public class NoProxy
{
    public static void main(String[] argv)
    throws Exception
    {
        StsClient client = StsClient.create();
        
        GetCallerIdentityRequest request = GetCallerIdentityRequest.builder().build();
        GetCallerIdentityResponse response = client.getCallerIdentity(request);
        
        System.out.println("account: " + response.account());
        System.out.println("user id: " + response.userId());
        System.out.println("arn:     " + response.arn());
    }
}
