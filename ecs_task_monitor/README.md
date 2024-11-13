A Lambda that responds to ECS task state change events, capturing the status and any
messages for stopped tasks. This is needed because the `ListTasks` and `DescribeTasks`
API calls do not retain information about stopped tasks for more than an hour or so.

Example output:

```
{
    "clusterName": "Example",
    "serviceName": "Example",
    "taskId": "5b64c49eb10e4b4bbeb051b02a02c58a",
    "taskDefinitionArn": "arn:aws:ecs:us-east-1:123456789012:task-definition/Example:3",
    "startedAt": "2024-11-13T22:17:16.469Z",
    "stoppedAt": "2024-11-13T22:23:07.955Z",
    "stopCode": "ServiceSchedulerInitiated",
    "stoppedReason": "Task failed ELB health checks in (target-group arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/Example/7a7a1fcbd0455d4b)",
    "containers": [
        {
            "name": "Example",
            "image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/example-webservice:latest",
            "imageDigest": "sha256:2f66438e209d4c2e638a26409ad1e5214eb2ee438dd4592820466fe7f4ecb820",
            "exitCode": 0
        }
    ]
}
```

Deploy with the provided CloudFormation template. You can change the name of the Lambda
if you like; all other resources depend on that name.

As implemented, the Lambda triggers on any task-stop events. You can add additional logic
to either the Lambda or the EventBridge rule to limit those executions. Unless you have a
large number of tasks, updating the Lambda is probably the easiest way to do this. For
reference, here's a sample event passed to the Lambda:

```
{
    "version": "0",
    "id": "95fb0ab4-e6f9-ba18-da16-ea0a3191d1b4",
    "detail-type": "ECS Task State Change",
    "source": "aws.ecs",
    "account": "123456789012",
    "time": "2024-11-13T21:23:11Z",
    "region": "us-east-1",
    "resources": [
        "arn:aws:ecs:us-east-1:123456789012:task/Example/cdd887a827a4432db19f6059310a4817"
    ],
    "detail": {
        "attachments": [
            {
                "id": "254e29d7-a6b7-4909-b9e8-fdee8f440883",
                "type": "elb",
                "status": "DELETED",
                "details": []
            },
            {
                "id": "ad48c228-d0c0-4efc-9b82-6b7a18fbcd29",
                "type": "eni",
                "status": "DELETED",
                "details": [
                    {
                        "name": "subnetId",
                        "value": "subnet-00aad8cc4d100aa7d"
                    },
                    {
                        "name": "networkInterfaceId",
                        "value": "eni-09a9a44a344ae7c9a"
                    },
                    {
                        "name": "macAddress",
                        "value": "0a:ff:c6:fe:7f:0b"
                    },
                    {
                        "name": "privateDnsName",
                        "value": "ip-172-31-68-200.ec2.internal"
                    },
                    {
                        "name": "privateIPv4Address",
                        "value": "172.31.68.200"
                    }
                ]
            }
        ],
        "attributes": [
            {
                "name": "ecs.cpu-architecture",
                "value": "x86_64"
            }
        ],
        "availabilityZone": "us-east-1c",
        "clusterArn": "arn:aws:ecs:us-east-1:123456789012:cluster/Example",
        "connectivity": "CONNECTED",
        "connectivityAt": "2024-11-13T20:55:53.836Z",
        "containers": [
            {
                "containerArn": "arn:aws:ecs:us-east-1:123456789012:container/Example/cdd887a827a4432db19f6059310a4817/a6c1281f-db57-4b98-a55c-e2e7ebe749e5",
                "exitCode": 0,
                "lastStatus": "STOPPED",
                "name": "Example",
                "image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/example-webservice:latest",
                "imageDigest": "sha256:2f66438e209d4c2e638a26409ad1e5214eb2ee438dd4592820466fe7f4ecb820",
                "runtimeId": "cdd887a827a4432db19f6059310a4817-2171104572",
                "taskArn": "arn:aws:ecs:us-east-1:123456789012:task/Example/cdd887a827a4432db19f6059310a4817",
                "networkInterfaces": [
                    {
                        "attachmentId": "ad48c228-d0c0-4efc-9b82-6b7a18fbcd29",
                        "privateIpv4Address": "172.31.68.200"
                    }
                ],
                "cpu": "0",
                "managedAgents": [
                    {
                        "name": "ExecuteCommandAgent",
                        "status": "STOPPED"
                    }
                ]
            }
        ],
        "cpu": "512",
        "createdAt": "2024-11-13T20:55:49.725Z",
        "desiredStatus": "STOPPED",
        "enableExecuteCommand": true,
        "ephemeralStorage": {
            "sizeInGiB": 20
        },
        "executionStoppedAt": "2024-11-13T21:22:46.71Z",
        "group": "service:Example",
        "launchType": "FARGATE",
        "lastStatus": "STOPPED",
        "memory": "1024",
        "overrides": {
            "containerOverrides": [
                {
                    "name": "Example"
                }
            ]
        },
        "platformVersion": "1.4.0",
        "pullStartedAt": "2024-11-13T20:56:01.615Z",
        "pullStoppedAt": "2024-11-13T20:56:16.038Z",
        "startedAt": "2024-11-13T20:56:36.54Z",
        "startedBy": "ecs-svc/2770844949256052681",
        "stoppingAt": "2024-11-13T21:21:58.645Z",
        "stoppedAt": "2024-11-13T21:23:11.984Z",
        "stoppedReason": "Task stopped by user",
        "stopCode": "UserInitiated",
        "taskArn": "arn:aws:ecs:us-east-1:123456789012:task/Example/cdd887a827a4432db19f6059310a4817",
        "taskDefinitionArn": "arn:aws:ecs:us-east-1:123456789012:task-definition/Example:3",
        "updatedAt": "2024-11-13T21:23:11.984Z",
        "version": 9
    }
}
```
