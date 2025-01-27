################################################################################
#
# MIT No Attribution
#
# Copyright Chariot Solutions
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
################################################################################

package main

import (
	"context"
    "encoding/base64"
    "encoding/json"
    "errors"
    "fmt"
    "log"
    "os"
	"github.com/aws/aws-lambda-go/lambda"
    "github.com/aws/aws-sdk-go-v2/config"
    "github.com/aws/aws-sdk-go-v2/feature/dynamodb/attributevalue"
	"github.com/aws/aws-sdk-go-v2/service/dynamodb"
	"github.com/aws/aws-sdk-go-v2/service/dynamodb/types"
    "github.com/google/uuid"
)


const (
    ID_PARAM_NAME = "id"
    ID_FIELD_NAME = "id"
)


var bool_true bool = true   // needed because we have to pass as an address to some requests

var client *dynamodb.Client
var tableName string


func init() {
	cfg, err := config.LoadDefaultConfig(context.TODO())
	if err != nil {
		log.Fatalf("Unable to load SDK config: %v", err)
	}

    tableName = os.Getenv("DYNAMO_TABLE_NAME")
    if tableName == "" {
        panic("DYNAMO_TABLE_NAME not set")
    }
    log.Println("table name: ", tableName)

	client = dynamodb.NewFromConfig(cfg)
}


func main() {
	lambda.Start(HandleRequest)
}


func HandleRequest(ctx context.Context, event *Event) (*Response, error) {
    log.Println("received", *event.HttpMethod, *event.RequestPath)
    id, err := extractOrGenerateId(event)
    if err != nil {
        return errorResponse(400, err), nil
    }

    if *event.HttpMethod == "GET" {
        return doGet(ctx, id), nil
    } else if *event.HttpMethod == "POST" || *event.HttpMethod == "PUT" {
        return doUpsert(ctx, id, event), nil
    } else {
        // any other methods should be blocked at API Gateway
        return errorResponse(400, errors.New(fmt.Sprintf("unsupported method:", *event.HttpMethod))), nil
    }
}


func extractOrGenerateId(event *Event) (string, error) {
    if *event.HttpMethod == "POST" {
        id := uuid.NewString()
        log.Println("generated ID for POST:", id)
        return id, nil
    }

    if event.PathParameters != nil {
        id := (*event.PathParameters)[ID_PARAM_NAME]
        if id != "" {
            return id, nil
        }
    }

    log.Println("unable to extract ID from path")
    return "", errors.New("unable to extract ID from path")
}


func doGet(ctx context.Context, id string) *Response {
    key_attr, err := attributevalue.Marshal(id)
    if err != nil {
        return errorResponse(500, err)
    }

    req := dynamodb.GetItemInput {
        TableName:      &tableName,
        Key:            map[string]types.AttributeValue { ID_FIELD_NAME: key_attr },
        ConsistentRead: &bool_true,
    }

    rsp, err := client.GetItem(ctx, &req)
    if err != nil {
        return errorResponse(500, err)
    }
    if len(rsp.Item) > 0 {
        return successResponse(rsp.Item)
    }
    return errorResponse(404, errors.New(fmt.Sprint("no such item: ", id)))
}


func doUpsert(ctx context.Context, id string, event *Event) *Response {
    body, err := extractAndParseBody(event)
    if err != nil {
        return errorResponse(500, err)
    }
    (*body)[ID_FIELD_NAME] = id

    item, err := attributevalue.MarshalMap(*body)
    if err != nil {
        return errorResponse(500, err)
    }

    req := dynamodb.PutItemInput {
        TableName:      &tableName,
        Item:           item,
    }
    _, err = client.PutItem(ctx, &req)
    if err != nil {
        return errorResponse(500, err)
    }
    return successResponse(item)
}


func extractAndParseBody(event *Event) (*map[string]interface{any}, error) {
    result := make(map[string]interface{any})
    if event.Body == nil {
        // the ID will be added by caller, so missing body just means no data
        return &result, nil
    }

    body := *event.Body
    if (event.IsBase64Encoded != nil) && *event.IsBase64Encoded {
        decoded, err := base64.StdEncoding.DecodeString(body)
        if err != nil {
            return nil, err
        }
        body = string(decoded)
    }
    err := json.Unmarshal([]byte(body), &result)
    return &result, err
}


func successResponse(item map[string]types.AttributeValue) *Response {
    unmarshaled := make(map[string]interface{any})
    err := attributevalue.UnmarshalMap(item, &unmarshaled)
    if err != nil {
        return errorResponse(500, err)
    }

    jsonified, err := json.Marshal(unmarshaled)
    if err != nil {
        return errorResponse(500, err)
    }

    response := Response {
        StatusCode:         "200",
        Headers:            map[string]string {
                                "Content-Type": "application/json",
                            },
        IsBase64Encoded:    false,
        Body:               string(jsonified),
    }
    return &response
}


func errorResponse(status_code int, err error) *Response {
    response := Response {
        StatusCode:         fmt.Sprint(status_code),
        Headers:            map[string]string {
                                "Content-Type": "text/plain",
                            },
        IsBase64Encoded:    false,
        Body:               err.Error(),
    }
    return &response
}
