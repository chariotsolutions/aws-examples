import cdk = require('@aws-cdk/core');
import iam = require('@aws-cdk/aws-iam');
import sqs = require('@aws-cdk/aws-sqs');

import { StandardQueue, STANDARD_CONSUMER_PERMISSIONS, STANDARD_PRODUCER_PERMISSIONS } from './standard_queue';

export class MultiQueueStack extends cdk.Stack {
  constructor(scope: cdk.Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // good habit: create "self" as reference to "this" so it can be used inside functions
    const self = this;

    const q1 = new StandardQueue(self, "Foo", {
        queueName: "Foo"
    })

    const q2 = new StandardQueue(self, "Bar", {
        queueName: "Bar"
    })

    const q3 = new StandardQueue(self, "Baz", {
        queueName: "Baz"
    })

    // rather than force use of the queue-specific policies, we'll create
    // combined policies

    const combinedConsumerPolicy = new iam.ManagedPolicy(self, "ConsumerPolicy", {
        managedPolicyName:  "SQS-" + self.stackName + "-Consumer",
        description:        "Attach this policy to consumers of any of the queues managed by " + self.stackName,
        statements:         [
                                new iam.PolicyStatement({
                                    effect:     iam.Effect.ALLOW,
                                    actions:    STANDARD_CONSUMER_PERMISSIONS,
                                    resources:  [
                                                    q1.mainQueue.queueArn,
                                                    q1.deadLetterQueue.queueArn,
                                                    q2.mainQueue.queueArn,
                                                    q2.deadLetterQueue.queueArn,
                                                    q3.mainQueue.queueArn,
                                                    q3.deadLetterQueue.queueArn
                                                ]
                                })
                            ]
    })

    const combinedProducerPolicy = new iam.ManagedPolicy(self, "ProducerPolicy", {
        managedPolicyName:  "SQS-" + self.stackName + "-Producer",
        description:        "Attach this policy to producers for any of the queues managed by " + self.stackName,
        statements:         [
                                new iam.PolicyStatement({
                                    effect:     iam.Effect.ALLOW,
                                    actions:    STANDARD_PRODUCER_PERMISSIONS,
                                    resources:  [
                                                    q1.mainQueue.queueArn,
                                                    q2.mainQueue.queueArn,
                                                    q3.mainQueue.queueArn
                                                ]
                                })
                            ]
    })

    const appRole = new iam.Role(self, "ApplicationRole", {
        roleName:        self.stackName + "-ApplicationRole",
        assumedBy:       new iam.ServicePrincipal('ec2.amazonaws.com'),
        managedPolicies: [ combinedProducerPolicy ]
    })

  }
}
