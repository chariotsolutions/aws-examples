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
