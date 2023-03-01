This directory contains examples showing how to use AWS X-Ray with Glue jobs.

* `example-1.py`

  A Python "shell job" that uses the AWS SDK to write segments directly to X-Ray.

* `example-2.py`

  A Python "shell job" that uses the X-Ray SDK, along with a custom emitter that
  avoids the need for a daemon.

* `example-3.py`

  A Python driver program that defines segments around PySpark operations. Uses
  the X-Ray SDK with a custom emitter.

* `example-4.py`

  A Python driver program that writes explicit segments for a Pandas UDF (in
  addition to using the X-Ray SDK for overal operation tracing).

You should be able to run each of these scripts from the Console, without setting
any parameters. They should take a minute or two to run.

When the script completes, look for its trace in the X-Ray Console (I recommend
using the [new](https://console.aws.amazon.com/cloudwatch/home#xray:traces/query)
Console page, under CloudWatch, rather than the legacy page).



## Deployment

Because this example requires a pre-populated S3 bucket, it is deployed using
a shell script:

```
scripts/deploy.sh BUCKET_NAME STACK_NAME
```

* `BUCKET_NAME` is the name of an S3 bucket that will be created to hold both
  scripts and data.

* `STACK_NAME` is the name for the CloudFormation stack that defines the Glue
  jobs. Each job will have the stack name prepended to its name.

To undeploy, use the counterpart shell script:

```
scripts/undeploy.sh BUCKET_NAME STACK_NAME
```
