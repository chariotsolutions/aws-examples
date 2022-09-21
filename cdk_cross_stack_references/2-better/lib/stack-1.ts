import * as cdk from 'aws-cdk-lib';
import * as ecs from "aws-cdk-lib/aws-ecs";
import * as logs from "aws-cdk-lib/aws-logs";
import * as ssm from "aws-cdk-lib/aws-ssm";
import { Construct } from 'constructs';


export interface Stack_1_Props extends cdk.StackProps {

  /** The name of the task definition. */
  readonly taskDefinitionName: string;

  /** Where we save the ARN for the task definition, so that it can be consumed later */
  readonly taskDefinitionArnExportPath: string;
}


export class Stack_1 extends cdk.Stack {

  constructor(scope: Construct, id: string, props: Stack_1_Props) {
    super(scope, id, props);

    const logGroup = new logs.LogGroup(this, "Logs", {
      logGroupName:   "/ecs/" + props.taskDefinitionName,
      removalPolicy:  cdk.RemovalPolicy.DESTROY,
    });

    const taskDefinition = new ecs.FargateTaskDefinition(this, 'TaskDefinition', {
      family:         props.taskDefinitionName,
      cpu:            256,
      memoryLimitMiB: 512,
    });

    const mainContainer = taskDefinition.addContainer("MainContainer", {
        image:        ecs.ContainerImage.fromRegistry("hello-world:latest"),
        logging:      ecs.LogDriver.awsLogs({
                        logGroup:     logGroup,
                        streamPrefix: "main-",
                      }),
    });

    const ssmParameter = new ssm.StringParameter(this, 'TaskDefinitionArnParameter', {
       parameterName:   props.taskDefinitionArnExportPath,
       stringValue:     taskDefinition.taskDefinitionArn,
    });
  }
}

