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
