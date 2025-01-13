Lambda to deconstruct CloudTrail files and write the individual records to a Kinesis Data Stream.

To build and deploy:

1. Run [cloudformation.yml](cloudformation.yml) to create the basic infrastructure.

   This template creates the following resources:

     * An SQS queue and dead-letter queue, to receive S3 notifications.
     * A Lambda and related resources (execution role, log group, trigger) to handle those notifications.
     * A Kinesis Data Stream to receive events. By default this has 1 shard and retains records for 24 hours.

   You must provide the name and prefix of the CloudTrail bucket, using parameters `CloudTrailBucket` and
   `CloudTrailBucketPrefix`. The latter is used to restrict access to files in the source bucket; it defaults
   to blank, meaning that the Lambda can access any files in the bucket. If provided, it must include a
   trailing slash (eg: `AWSLogs/`).

   There are also parameters used to name each of the created resources, and for configuration of the Kinesis
   stream. These all have defaults.

2. Deploy the Lambda

   The CloudFormation template creates a Lambda with a dummy handler. You can either manually create a ZIP
   file from the contents of the `lambda` directory, or use _make_:

   ```
   make deploy
   ```

   If you changed the name of the Lambda in step 1, you'll need to tell _make_ the actual name:

   ```
   make deploy LAMBDA_NAME=Your_Lambda_Name
   ```

3. Update the CloudTrail bucket's notification policy to send events to the notification queue.

   This is a manual process, because CloudFormation can only attach a notification when it creates the
   bucket. In the case of CloudTrail, you will have already created this bucket when you set up the
   trail.

   In the Console, open the bucket, go to the Properties tab, scroll down to "Event notifications",
   and click "Create event notification". Enter a name for the notification, the prefix where your
   CloudTrail log files are stored, select "All object create events", and set the destination as
   the SQS queue created by CloudFormation.


You can also run the transformation locally, passing either an S3 URL or a local filename along with
the name of the Kinesis stream. You must have the `boto3` library installed.

```
python lambda s3://com-example-cloudtrail/AWSLogs/o-unx82b27e/123456789012/CloudTrail/us-east-1/2024/09/05/123456789012_CloudTrail_us-east-1_20240905T1725Z_Rr5pMUQHMIcl1qD4.json.gz  cloudtrail_events
```

```
python lambda /tmp/123456789012_CloudTrail_us-east-1_20240905T0230Z_Hvjj6jOPNs4RVsVB.json.gz cloudtrail_events
```
