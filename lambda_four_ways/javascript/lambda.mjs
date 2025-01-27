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

import { v4 as uuidv4 } from 'uuid';
import { DynamoDBClient, GetItemCommand, PutItemCommand } from "@aws-sdk/client-dynamodb";
import { marshall as ddbMarshall, unmarshall as ddbUnmarshall } from "@aws-sdk/util-dynamodb";


const client = new DynamoDBClient();

const tableName = process.env.DYNAMO_TABLE_NAME


export const handler =  async (event, context) => {
  let httpMethod = event["httpMethod"];
  let path = event["path"];
  console.info("handling ", httpMethod, " ", path);

  let id = extractOrGenerateId(httpMethod, event);
  if (! id) {
    return failure(400, "unable to extract ID from path")
  }

  if (httpMethod == "GET") {
    return doGet(id);
  }
  else if ((httpMethod == "PUT") || (httpMethod == "POST")) {
    return doUpsert(id, event);
  }

  console.error("received unsupported method: " + httpMethod + "; should have been blocked at API Gateway");
  return failure(400, "unsupported method: " + httpMethod);
};


let extractOrGenerateId = (httpMethod, event) => {
  if (httpMethod == "POST") {
    let id = uuidv4();
    console.info("created ID for post: ", id);
    return id;
  }
  return event["pathParameters"]?.["id"]
}


let doGet = async (id) => {
  const request = {
    TableName:      tableName,
    Key:            { "id": { S: id }},
    ConsistentRead: true,
  }
  const command = new GetItemCommand(request);
  const response = await client.send(command);
  if (response.Item) {
    return success(response.Item);
  }
  return failure(404, "no such item: " + id);
}


let doUpsert = async (id, event) => {
  let body = event["body"];
  if (event["isBase64Encoded"]) {
    body = Buffer.from(body, 'base64').toString('utf8');
  }
  let data = JSON.parse(body);
  data["id"] = id;
  let item = ddbMarshall(data);

  const request = {
    TableName:      tableName,
    Item:           item,
  }
  const command = new PutItemCommand(request);
  await client.send(command);
  return success(item);
}


let success = async(item) => {
  return {
    statusCode: 200,
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(ddbUnmarshall(item)),
  };
}


let failure = async(statusCode, message) => {
  return {
    statusCode: statusCode,
    headers: {
      'Content-Type': 'text/plain'
    },
    body: message,
  };
}
