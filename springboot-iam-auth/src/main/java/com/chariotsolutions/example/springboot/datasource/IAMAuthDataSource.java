package com.chariotsolutions.example.springboot.datasource;

import java.sql.Connection;
import java.sql.SQLException;

import org.postgresql.ds.PGSimpleDataSource;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.amazonaws.auth.DefaultAWSCredentialsProviderChain;
import com.amazonaws.regions.DefaultAwsRegionProviderChain;
import com.amazonaws.services.rds.auth.GetIamAuthTokenRequest;
import com.amazonaws.services.rds.auth.RdsIamAuthTokenGenerator;


/**
 *  Retrieves IAM-generated credentials for the configured user.
 *  <p>
 *  Before you can use this, you must grant <code>rds_iam</code> to the user.
 */
public class IAMAuthDataSource
extends PGSimpleDataSource
{
    private final static long serialVersionUID = 1L;
    
    private Logger logger = LoggerFactory.getLogger(getClass());


    @Override
    public Connection getConnection(String user, String password)
    throws SQLException
    {
        // I'd like to do this in constructor, but it can throw SQLException
        setProperty("ssl", "true");
        setProperty("sslmode", "require");
        
        logger.debug("requesting IAM token for user {}", user);

        // adapted from https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/UsingWithRDS.IAMDBAuth.Connecting.Java.html
        RdsIamAuthTokenGenerator generator = RdsIamAuthTokenGenerator.builder()
            .credentials(new DefaultAWSCredentialsProviderChain())
            .region((new DefaultAwsRegionProviderChain()).getRegion())
            .build();

        GetIamAuthTokenRequest request = GetIamAuthTokenRequest.builder()
            .hostname(getServerName())
            .port(getPortNumber())
            .userName(user)
            .build();

        String authToken = generator.getAuthToken(request);

        return super.getConnection(user, authToken);
    }
}
