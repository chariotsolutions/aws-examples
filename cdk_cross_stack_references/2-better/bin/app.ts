#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';

import { Stack_1, Stack_1_Props } from '../lib/stack-1';
import { Stack_2, Stack_2_Props } from '../lib/stack-2';


const env = { account: process.env.CDK_DEFAULT_ACCOUNT, region: process.env.CDK_DEFAULT_REGION }

const taskDefinitionArnExportPath = "/cdk/parameters/2-better/taskDefinitionArn";

const app = new cdk.App();

const stack_1 = new Stack_1(app, "Stack1", {
    env: env,
    taskDefinitionName: "example-2-better",
    taskDefinitionArnExportPath: taskDefinitionArnExportPath,
});

const stack_2 = new Stack_2(app, "Stack2", {
    env: env,
    taskDefinitionArnExportPath: taskDefinitionArnExportPath,
});
