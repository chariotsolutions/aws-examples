# Lambda Four Ways

Implements the same task -- reading and writing DynamoDB -- using four different languages: Go, Java, JavaScript (Node), and Python.

See [this blog post]https://chariotsolutions.com/blog/post/lambda-four-ways/) for more information.


## Prerequisites

These instructions are written for Linux, and assume that you have the following
tools installed:

* `make` (I use Gnu Make, but don't do anything tricky; other Makes should work).
* The AWS CLI.
* The compiler / runtime for the language(s) you use.
* For Java, the Maven build tool.

You must also have appropriate AWS permissions. These include the permissions to
create the CloudFormation stack and all of the resources that it defines, as well
as permission to upload the deployment bundle to S3 and update the Lambda's code.


## Building

Each version lives in its own directory, and has a Makefile with the following targets:

* `build` invokes the compiler or other tools to build the deployment bundle. You
  will not normally invoke this target directly, but use either `upload` or `deploy`,
  both of which invoke this target as a first step.

* `upload` uploads the deployment artifact to S3. You must use this target before
  deploying the CloudFormation script described below.

  This target uses environment variables to specify the bucket and key where the
  file should be uploaded:

  ```
  BUCKET=com-example-deployment KEY=lambda_four_ways/python/lambda.zip make upload 
  ```

* `deploy` uploads the deployment artifact to an existing Lambda function. You would
  use this target when making changes to the function implementation after creating
  it via CloudFormation.

  You can provide the name of the target Lambda via environment variable. By default,
  this name is `LambdaFourWays`, which is also the default for the CloudFormation
  template.

  ```
  LAMBDA_NAME=LambdaFourWays-Python make deploy
  ```


## Deploying

There's a single CloudFormation template to deploy all four versions. Note that you
must have already built the Lambda deployment bundle, and uploaded it to S3.

The following parameters are reuuired:

* `Runtime`

  The runtime used for this deployment. Pick the value appropriate to your language
  (these values are the latest versions as-of the time of writing):

  * Go: `provided.al2023`
  * Java: `java21`
  * JavaScript: `nodejs20.x`
  * Python: `python3.12`

* `DeploymentBucket`

  The name of the S3 bucket where you uploaded your deployment artifact.

* `DeploymentKey`

  The key of the deployment artifact within that bucket.

The following parameters have defaults, but you may change them:

* `LambdaName`

  The name of the Lambda and any related resources (such as its execution role).
  The default value is `LambdaFourWays`, which won't work if you're deploying
  multiple versions (instead, I recommend `LambdaFourWays-Python`, etc).

* `TableName`

  The name of the DynamoDB table. Default is `lambda_four_ways`.

  This table is created with provisioned capacity of 5 RCU and 5 WCU. These values
  are within the "permanent free tier" for DynamoDB, but you will still be charged
  for data storage and data transfer.

* `Memory`

  The amount of memory (and therefore CPU) allocated to the Lambda. The default
  value of 1024 MB gives you slighly over half of a virtual CPU.


## Running

This Lambda performs the following functions:

* `GET /id` retrieves an existing item by ID (or returns a 404 status if the item
  does not exist).

  ```
  curl 'https://pcip9m0ry6.execute-api.us-east-1.amazonaws.com/12df8968-2857-456e-be66-36acfe0195ba'
  ```

* `POST /` creates a new item, returning the item contents with the `id` field
  populated.

  ```
  curl -XPOST -d '{"foo": 123, "bar":456}' 'https://pcip9m0ry6.execute-api.us-east-1.amazonaws.com/'
  ```

* `PUT /id` overwrites an existing item with the given ID (and, because this is
  sample code, it can also be used to create a new item with that ID).

  ```
  curl -XPUT -d '{"foo": 123, "bar":456, "baz": [9, 8]}' 'https://pcip9m0ry6.execute-api.us-east-1.amazonaws.com/12df8968-2857-456e-be66-36acfe0195ba'
  ```


## Implementation Notes

### Go

There isn't, to the best of my knowledge, a prebuilt library of Go types for Lambda request
and response objects, so this Lambda defines its own in `types.go`. The API Gateway request
has lots of fields, but this Lambda only uses a few of them. Fortunately, the Go JSON
marshaller will ignore any fields in the source that don't match annotated fields in the
corresponding struct.


### Java

I have chosen to handle the source event as a `Map<String,Object>`, rather than using the
`APIGatewayV2HTTPEvent` from the [aws-lambda-java-events](https://central.sonatype.com/artifact/com.amazonaws/aws-lambda-java-events)
library. To be honest, I don't even know if that event structure is intended to support
the API Gateway integration that I'm using: it's missing several of the top-level elements
of the actual event JSON, has items with different names, and does not appear to populate
nested structures.


### JavaScript

I use the "bare bones" clients (ie, creating a command object and sending it, versus a
single-step method call), introduced with the v3 SDK. This style is supposedly lower
overhead, and my timings have show that to be true.


### Python

The Boto3 library provides a high-level "document" interface to DynamoDB. However, the
documents that it returns can contain objects of type `Decimal` and `set`, which the
built-in `json` library can't serialize. Rather than use a third-party library, I use
a custom `JSONEncoder` that will handle these two types. `Decimal` values turn into
either `float` or `int`, depending on whether or not they have digits to the right of
the decimal place; `set` values turn into lists.
