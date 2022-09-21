This example demonstrates the problem with cross-stack references, including how easy they are to create
using CDK. It exists to support [this blog post](https://chariotsolutions.com/?post_type=blog&p=18174&preview=true).

The example is a (highly) simplified two-stack deployment. The first stack creates an ECS
task, while the second triggers a Lambda when that task completes. This is a standard
pattern in data pipelines, where you might have multiple operations that have to run after
some initial process.

There are three variants of this deployment:

* `1-broken`

  The first stack exposes the ECS task definition resource, and CDK the app passes it to
  the second, which uses the task definition's ARN to create an EventBridge trigger.

  This can be deployed once. If you make any changes to Stack1, for example increasing
  the memory given to the ECS task, you will be unable to deploy that change. You won't
  see the actual error unless you're watching the CLI deploy, but the CloudFormation
  Events tab will tell you that a particular export is in use by Stack2.

* `2-better`

  This variant saves the task definition ARN in Parameter Store, and then references
  that Parameter Store entry from Stack2.

  This effectively breaks the cross-stack reference, allowing Stack1 to be redeployed,
  but at the cost of allowing the two stacks to get out-of-sync. Using this approach
  you must always deploy both at the same time, or your Lambda won't be triggered.

* `3-best`

  This variant doesn't export the task definition. Instead, it exports the name of the
  task definition _family_ (which is actually controlled by `app.ts`), and Stack2 uses
  that to construct a "prefix" event rule.

  This is arguably the best because it reframes the problem and makes it go away.
  Unfortunately, that's not always possible to do this.

**Note:** these examples are intended to highlight the relationships between stacks, and should
not be considered good usage examples for the CDK constructs involved. In particular, I let CDK
pick a lot of default values here, which I think is a bad idea for production scripts.


## Deploying

These are standard CDK projects. Assuming that you have CDK installed locally, the
steps to deploy are:

1. Go into whatever directory you want to deploy.
2. Run `npm install`
3. Run `cdk synth` to construct the templates for your environment (this allows you
   to review the templates; it can be skipped if you just want to deploy).
4. Run `cdk deploy --all` to perform the initial deployment.

You can then make a small change to the ECS task definition -- for example, changing
`memoryLimitMiB` from 512 to 1024 -- and then attempt to redeploy (step 4). For the
`1-broken` example, this deployment will fail; for the other two, it will succeed.

When done, run `cdk destroy --all` or delete the stacks from the CloudFormation Console.

**Note:** since these projects use the same name for their stacks, only one sub-project
can be deployed at a time; you will need to destroy any previous sub-project before
deploying a different one.


## Running

The point of these examples is to show problems with deployment. However, if you wish to
see the pipeline in action, I recommend my [ecs-run](https://github.com/kdgregory/aws-misc/blob/trunk/utils/ecs-run.py)
utility:

```
ecs-run.py example-2-better
```

Once the task finishes running, you should see the Lambda be invoked. It will write logs
to CloudWatch, including the invocation event.

**Note:** you will need to manually delete the CloudWatch log group used by the Lambda,
because I let the Lambda create that group (versus managing it with CDK, which I consider
a best practice for production stacks).
