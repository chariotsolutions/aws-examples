import cdk = require('@aws-cdk/core');
import iam = require('@aws-cdk/aws-iam');
import sqs = require('@aws-cdk/aws-sqs');

import { StandardQueue } from './standard_queue';

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

    const appRole = new iam.Role(self, "ApplicationRole", {
        roleName:        self.stackName + "-ApplicationRole",
        assumedBy:       new iam.ServicePrincipal('ec2.amazonaws.com'),
        managedPolicies: [ q1.producerPolicy, q2.producerPolicy, q3.producerPolicy ]
    })
  }
}
