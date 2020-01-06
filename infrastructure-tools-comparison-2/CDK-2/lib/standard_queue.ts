import cdk = require('@aws-cdk/core');
import iam = require('@aws-cdk/aws-iam');
import sqs = require('@aws-cdk/aws-sqs');


/**
*  Standard permissions for a queue consumer.
*/
export const STANDARD_CONSUMER_PERMISSIONS: string[] = [
    "sqs:ChangeMessageVisibility",
    "sqs:ChangeMessageVisibilityBatch",
    "sqs:DeleteMessage",
    "sqs:DeleteMessageBatch",
    "sqs:GetQueueAttributes",
    "sqs:GetQueueUrl",
    "sqs:ReceiveMessage"
];


/**
*  Standard permissions for a queue producer.
*/
export const STANDARD_PRODUCER_PERMISSIONS: string[] = [
    "sqs:GetQueueAttributes",
    "sqs:GetQueueUrl",
    "sqs:SendMessage",
    "sqs:SendMessageBatch"
];


/**
 *  Properties for configuring a standard queue.
 */
export interface StandardQueueConfig {
    /**
     *  The name of the primary queue. This is used to construct the name
     *  of the dead-letter queue and consumer/producer policies.
     */
    readonly queueName: string
}


/**
 *  Attributes exposed by a standard queue. These are the resources created
 *  by the construct; you can dig into those to extract attributes.
 */
export interface IStandardQueue  extends cdk.IResource {

  /**
   * The primary queue
   * @attribute
   */
  readonly mainQueue: sqs.Queue;

  /**
   * The dead letter queue
   * @attribute
   */
  readonly deadLetterQueue: sqs.Queue;

  /**
   * The consumer policy.
   * @attribute
   */
  readonly consumerPolicy: iam.ManagedPolicy;

  /**
   * The producer policy.
   * @attribute
   */
  readonly producerPolicy: iam.ManagedPolicy;

}


export class StandardQueue extends cdk.Construct {

  public readonly mainQueue: sqs.Queue;
  public readonly deadLetterQueue: sqs.Queue;
  public readonly consumerPolicy: iam.ManagedPolicy;
  public readonly producerPolicy: iam.ManagedPolicy;


  constructor(scope: cdk.Construct, id: string, props: StandardQueueConfig) {
    super(scope, id);

    this.mainQueue = new sqs.Queue(this, "Main", {
        queueName: props.queueName
    })

    this.deadLetterQueue = new sqs.Queue(this, "DLQ", {
        queueName: props.queueName + "-DLQ"
    })

    this.consumerPolicy = new iam.ManagedPolicy(this, "ConsumerPolicy", {
        managedPolicyName:  "SQS-" + props.queueName + "-Consumer",
        description:        "Attach this policy to consumers of " + props.queueName,
        statements:         [
                                new iam.PolicyStatement({
                                    effect:     iam.Effect.ALLOW,
                                    actions:    STANDARD_CONSUMER_PERMISSIONS,
                                    resources:  [
                                                    this.mainQueue.queueArn,
                                                    this.deadLetterQueue.queueArn
                                                ]
                                })
                            ]
    })

    this.producerPolicy = new iam.ManagedPolicy(this, "ProducerPolicy", {
        managedPolicyName:  "SQS-" + props.queueName + "-Producer",
        description:        "Attach this policy to producers for " + props.queueName,
        statements:         [
                                new iam.PolicyStatement({
                                    effect:     iam.Effect.ALLOW,
                                    actions:    STANDARD_PRODUCER_PERMISSIONS,
                                    resources:  [
                                                    this.mainQueue.queueArn
                                                ]
                                })
                            ]
    })
  }
}
