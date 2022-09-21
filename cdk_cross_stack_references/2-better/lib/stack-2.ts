import * as cdk from 'aws-cdk-lib';
import * as ecs from "aws-cdk-lib/aws-ecs";
import * as events from "aws-cdk-lib/aws-events";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as ssm from "aws-cdk-lib/aws-ssm";
import * as targets from "aws-cdk-lib/aws-events-targets";
import { Construct } from 'constructs';


export interface Stack_2_Props extends cdk.StackProps {

  /** Where we retrieve the ARN for the task definition. */
  readonly taskDefinitionArnExportPath: string;
}


export class Stack_2 extends cdk.Stack {

  constructor(scope: Construct, id: string, props: Stack_2_Props) {
    super(scope, id, props);

    const handler = new lambda.Function(this, 'TaskListener', {
      runtime:    lambda.Runtime.PYTHON_3_9,
      handler:    'index.handler',
      code:       lambda.Code.fromInline(
                  "import json\n" +
                  "\n" +
                  "def handler(event, context):\n" +
                  "    print(json.dumps(event))\n"
                  ),
    });

    const taskDefinitionArn = ssm.StringParameter.valueForStringParameter(this, props.taskDefinitionArnExportPath);

    const rule = new events.Rule(this, "TaskListenerTrigger", {
      description:
        "Triggers the " + handler.functionName + " on ECS task completion",
      eventPattern: {
        source: ["aws.ecs"],
        detailType: ["ECS Task State Change"],
        detail: {
          lastStatus: ["STOPPED"],
          taskDefinitionArn: [taskDefinitionArn],
        },
      },
    });

    rule.addTarget(new targets.LambdaFunction(handler, {}));
  }
}
