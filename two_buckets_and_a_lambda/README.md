# Two Buckets and a Lambda: a pattern for S3 file transformation

This is the example code for [this blog post](#). It implements a simple web-app in
addition to the actual processor Lambda.

![Architecture Diagram](static/images/webapp-architecture.png)


## Usage

First, run the deployment script (you must have the CLI installed):

```
./deploy.sh STACK_NAME BASE_BUCKET_NAME
```

`STACK_NAME` is the name for your stack; it must be unique within the account/region.

`BASE_BUCKET_NAME` is used to name the three buckets; the suffixes `-uploads`, `-archive`,
and `-static` will be applied to it. Bucket names must be globally unique; I recommend a
reverse domain name that includes the stack name: `com-example-mystack` (note that bucket
names must be lowercase).

This script should take less than five minutes to run. However, it uses the CLI's "wait"
command, which doesn't time out until an hour has elapsed. You can either get the status
of the stack via the CLI in another window, or watch the creation events in the console.


## Implementation Notes
