package com.chariotsolutions.example;

import java.nio.charset.StandardCharsets;
import java.util.Base64;
import java.util.Collections;
import java.util.Map;
import java.util.UUID;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.amazonaws.services.lambda.runtime.Context;
import com.amazonaws.services.lambda.runtime.RequestHandler;
import com.amazonaws.services.lambda.runtime.events.APIGatewayV2HTTPResponse;

import software.amazon.awssdk.enhanced.dynamodb.*;
import software.amazon.awssdk.enhanced.dynamodb.document.*;


/**
 *  Handler for a Lambda that provides access to DynamoDB.
 */
public class DynamoLambda
implements RequestHandler<Map<String,Object>,APIGatewayV2HTTPResponse>
{
    private final static String TABLE_NAME_ENVAR = "DYNAMO_TABLE_NAME";
    private final static String ID_FIELD_NAME = "id";

    private Logger logger = LoggerFactory.getLogger(getClass());

    private DynamoDbTable<EnhancedDocument> table;


    public DynamoLambda()
    {
        DocumentTableSchema  schema = TableSchema.documentSchemaBuilder()
                                      .addIndexPartitionKey(TableMetadata.primaryIndexName(),"id", AttributeValueType.S)
                                      .attributeConverterProviders(AttributeConverterProvider.defaultProvider())
                                      .build();
        String table_name = System.getenv(TABLE_NAME_ENVAR);
        if (table_name == null)
            throw new RuntimeException("must specify DynamoDB table name in envar " + TABLE_NAME_ENVAR);

        logger.info("DynamoDB table name: {}", table_name);
        DynamoDbEnhancedClient client = DynamoDbEnhancedClient.create();
        table = client.table(table_name, schema);
    }


    @Override
    public APIGatewayV2HTTPResponse handleRequest(Map<String,Object> event, Context context)
    {
        String httpMethod = (String)event.get("httpMethod");
        String path = (String)event.get("path");
        logger.info("invoked with method {}, path {}", httpMethod, path);

        String id = extract_or_generate_id(httpMethod, event);
        if ("GET".equalsIgnoreCase(httpMethod))
        {
            return doGet(id);
        }
        else
        {
            return doUpsert(id, event);
        }
    }


    private String extract_or_generate_id(String httpMethod, Map<String,Object> event)
    {
        if ("POST".equalsIgnoreCase(httpMethod))
        {
            String id = UUID.randomUUID().toString();
            logger.info("generated ID for POST: {}", id);
            return id;
        }

        Map<String,String> pathParameters = (Map<String,String>)event.get("pathParameters");
        if (pathParameters != null)
        {
            String id = pathParameters.get("id");
            if (id != null)
                return id;
        }

        throw new RuntimeException("unable to extract ID from event");
    }


    private APIGatewayV2HTTPResponse doGet(String id)
    {
        EnhancedDocument item = table.getItem(Key.builder().partitionValue(id).build());
        if (item == null)
            return failure(404, "no such item: " + id);
        else
            return APIGatewayV2HTTPResponse.builder()
                   .withStatusCode(200)
                   .withBody(item.toJson())
                   .build();
    }


    private APIGatewayV2HTTPResponse doUpsert(String id, Map<String,Object> event)
    {
        String rawBody = (String)event.get("body");
        boolean isBase64 = ((Boolean)event.getOrDefault("isBase64Encoded",Boolean.FALSE)).booleanValue();

        String body = isBase64
                      ? new String(Base64.getDecoder().decode(rawBody), StandardCharsets.UTF_8)
                      : rawBody;
        EnhancedDocument item = EnhancedDocument.fromJson(body);
        item = item.toBuilder()
              .putString(ID_FIELD_NAME, id)
              .build();
        table.putItem(item);
        return success(item);
    }


    private static APIGatewayV2HTTPResponse success(EnhancedDocument item)
    {
        return APIGatewayV2HTTPResponse.builder()
               .withStatusCode(200)
               .withHeaders(Collections.singletonMap("Content-Type", "application/json"))
               .withBody(item.toJson())
               .build();
    }


    private static APIGatewayV2HTTPResponse failure(int statusCode, String reason)
    {
        return APIGatewayV2HTTPResponse.builder()
               .withStatusCode(statusCode)
               .withHeaders(Collections.singletonMap("Content-Type", "text/plain"))
               .withBody(reason)
               .build();
    }
}
