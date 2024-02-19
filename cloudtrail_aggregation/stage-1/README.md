# Stage 1: Daily Aggregation

This stage takes a day's worth of files produced by CloudTrail, and writes them as
one or more NDJSON (newline-delimited JSON) files in a different destination.

The core challenge of this step is to identify the files belonging to a given day.
This requires recursively calling the `ListObjectsV2` API, to retrieve the list of
accounts and regions within those accounts.


## Prerequisites

You must have a bucket containing raw CloudTrail log files. This will normally be
created at the time you create your trail. If it's in a different account from the
one running this Lambda, it must have a bucket policy that allows `s3:ListBucket`
and `s3:GetObject` for the invoking account.

You must also have a bucket that will receive the aggregated files. If you create
this bucket in a different account, it must have a bucket policy that allows
s3:PutObject` for the invoking account.


## CloudFormation

You can deploy this Lambda using [CloudFormation](cloudformation.yml). This template
creates the following resources:

* The SQS queue used to trigger the Lambda, with an associated dead-letter queue.

* A Lambda to perform the transform, along with its execution role, log group, and
  trigger. Note that the Lambda has dummy source code; you must explicitly update
  with the contents of [lambda.py](lambda.py).

* An EventBridge Scheduler rule (along with its role) that writes a message to the
  SQS queue at 1 AM UTC.

For convenience, the script outputs the URL of the SQS queue.


## Triggering the Lambda

As deployed, the Lambda will be triggered by EventBridge at 1 AM UTC every day.

You can also use the Console to push a JSON message like the this:

```
{
  "month": 2,
  "day": 8,
  "year": 2024
}
```

And finally, to process a backlog of days, use the [populate_queue.py](populate_queue.py) script.


## Creating an Athena table

The file [table.ddl](table.ddl) contains DDL for the daily aggregation table. Edit
this file, replacing `BUCKET` and `BASE_PREFIX` with the actual values for your data
(eg, `cloudtrail-daily`), then paste into an Athena query window.

Note: this DDL is based on that produced from the CloudTrail Console, with changes to
partitioning.
