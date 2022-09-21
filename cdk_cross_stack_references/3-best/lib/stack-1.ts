import * as cdk from 'aws-cdk-lib';
import * as ecs from "aws-cdk-lib/aws-ecs";
import * as logs from "aws-cdk-lib/aws-logs";
import { Construct } from 'constructs';


export interface Stack_1_Props extends cdk.StackProps {

  /** The name of the task definition. */
  readonly taskDefinitionName: string;
}


export class Stack_1 extends cdk.Stack {

  public readonly taskDefinitionFamilyName: string;

  constructor(scope: Construct, id: string, props: Stack_1_Props) {
    super(scope, id, props);

    // we're just using the provided name here, but it's good practice to expose
    // the variable separately so that we have the ability to change it
    this.taskDefinitionFamilyName = props.taskDefinitionName;

    // note: this is an example stack so we don't want to preserve the log group
    //       when the stack is deleted
    const logGroup = new logs.LogGroup(this, "Logs", {
      logGroupName:   "/ecs/" + props.taskDefinitionName,
      removalPolicy:  cdk.RemovalPolicy.DESTROY,
    });

    const taskDefinition = new ecs.FargateTaskDefinition(this, 'TaskDefinition', {
      family:         this.taskDefinitionFamilyName,
      cpu:            256,
      memoryLimitMiB: 1024,
    });

    const mainContainer = taskDefinition.addContainer("MainContainer", {
        image:        ecs.ContainerImage.fromRegistry("hello-world:latest"),
        logging:      ecs.LogDriver.awsLogs({
                        logGroup:     logGroup,
                        streamPrefix: "main-",
                      }),
    });
  }
}

