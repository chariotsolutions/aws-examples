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
