CloudFormation templates to support a presentation on EventBridge.

## ec2_tag_check.yml

Demonstrates the "traditional" (aka CloudWatch Events) capability of triggering
actions based on system events. In this case, running a Lambda whenever an EC2
instance starts up, to verify that it's properly tagged. The example sends a
message to SNS if it isn't, but it could be more authoritarian and terminate
the instance.

Configuration parameters:

* `ExpectedTags`: a comma-separate list of tags that EC2 instances are expected
  to have.

Creates the following AWS objects:

* A Lambda, with associated execution role and CloudWatch log group.
* An EventBridge rule to trigger that Lambda.
* A SNS topic that receives notifications when an EC2 instance is not
  properly tagged.

To try it out, you'll need to start up an instance, with or without the expected
tags. You will also need to subscribe something to the SNS topic; email is best.


## event_dispatch.yml

Demonstrates how rules can direct events to different recipients. There is one
"injection" Lambda, that sends its invocation event to EventBridge, and two
"handler" Lambdas that respond to events by printing them. The EventBridge rules
dispatch based on the `eventType` field inside the event.

The "injection" Lambda also demonstrates the need to examine the returned status
from PutEvents, and respond to any errors. It the case of this example, failures
are dumped into an SQS queue.

Creates the following AWS objects, all named based on the CloudFormation stack:

* An Event Bus
* Three Lambdas, along with associated log groups and execution roles.
* An SQS queue, used to capture failed PutEvents calls.

Here are some sample events. Note that only three of them will be dispatched with
the provided rules.

```
{"eventType": "addToCart", "eventId": "2833f301-91a4-4c79-a4c6-ddcf190eb87a", "timestamp": "2021-08-03 07:05:36.044", "userId": "5356774a-51e5-4c48-85d8-b5ee52783802", "productId": "1068", "quantity": 8}
{"eventType": "updateItemQuantity", "eventId": "82651b5f-c1ad-4108-a1e0-ddca280cc7fc", "timestamp": "2021-08-03 07:06:49.044", "userId": "5356774a-51e5-4c48-85d8-b5ee52783802", "productId": "1068", "quantity": 10}
{"eventType": "checkoutStarted", "eventId": "d01274dc-6db9-4d02-88d4-37b0f6402eb2", "timestamp": "2021-08-03 07:06:55.044", "userId": "5356774a-51e5-4c48-85d8-b5ee52783802", "itemsInCart": 4, "totalValue": 81.5}
{"eventType": "checkoutComplete", "eventId": "fa5bfad9-1a13-483c-ae39-78e3aacf7ddc", "timestamp": "2021-08-03 07:07:05.044", "userId": "5356774a-51e5-4c48-85d8-b5ee52783802", "itemsInCart": 4, "totalValue": 81.5}
```


## clickstream_partitioning.yml

Demonstrates using EventBridge Pipes to partition a raw stream of events using a
value inside the data. In this case, the different streams of events are sent to
two Kinesis Firehose endpoints, but you could also direct them to a Lambda, or
inject them to a custom event bus.

### Generating events

Use [clickstream_generator.py] to generate the events. This program simulates
users taking action on an eCommerce website: looking at product pages, adding
items to their cart, and checking out.

To run this program, you must have the `boto3` library available on your Python
path, have an existing Kinesis stream, and credentials that allow writing to
this stream. You tell it the name of the stream, the number of users, number
of distinct products, and total number of events desired. It reports each batch
of events that it writes to the stream, and at the end reports the counts for
each event type.

```
./clickstream_generator.py NUM_EVENTS NUM_USERS NUM_PRODUCTS KINESIS_STREAM
```

So, to generate 1000 events, representing 200 users interacting with 100 products,
and writing them to a Kinesis stream named "Example":

```
> ./clickstream_generator.py 1000 200 100 Example

sending 499 events
sending 499 events
sending 2 events
events by type:
   productPage = 633
   addToCart = 192
   checkoutStarted = 97
   checkoutComplete = 77
   updateItemQuantity = 1
``

Note that there are events (`productPage`, `checkoutStarted`) that aren't used
by this example.

### Event transformation

Formatting the target event is one of the key call-outs from this example. Data
lakes want newline-delimited JSON (NDJSON), in which each JSON record takes a
single line.  This has historically been an issue with Kinesis Firehose, since
many data sources send multi-line, pretty-printed JSON, or omit a trailing newline.
The standard solution is to use a transformation Lambda in your Firehose, which
reformats the source record as NDJSON and appends a newline.

EventBridge Pipes, with its [transformations](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-pipes-input-transformation.html#eb-pipes-transform-input-issues),
seems like it should be a great solution. However, it turns out to be rather
painful to generate valid output, because transformations generate character
strings, not JSON. This has the following effects:

* If you don't transform at all, Firehose receives the source record, including
  all metadata and Base64-encoded data. This is unusable in a data lake.
* The simple `<$.data>` transformation, which appears to work if you use it
  in the Console, actually produces a record that's stripped of quotation marks,
  meaning that it's not valid JSON.
* The recommended workaround, `{"data": <$.data>}`, doesn't accurately 
  represent the source record.

Instead, you must construct the output record from individual fields of the source
record.  _But,_ you can't do this as a multi-line transform, because those newlines
will be in the output, and make a record that's unreadable by the Athena JSON SerDe.
And you must ensure that the trailing newline is part of the transformed record.

The solution that I used is a YAML multi-line string block that contains only a
single line. This avoids the need to escape all of the quotes inside the JSON
record, and it adds a newline at the end of the record.
of the record. 
