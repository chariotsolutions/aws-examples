This is a Lambda that will process CloudTrail log files from S3 and write the events into
an Elasticsearch cluster. This allows easy exploration and summarization, versus tools
such as AWS Athena.


## Building

This Lambda depends on the [`requests`](https://pypi.org/project/requests/) and
[`aws-requests-auth`](https://pypi.org/project/aws-requests-auth/) libraries. You
install them and their dependencies with `pip`:

```
pip3 install -t dist --system requests aws-requests-auth
```

The `--system` flag is only needed if you're running on a Debian variant (such as Ubuntu),
because they ignore the `-t` flag otherwise.

Next, copy the Lambda function code into the distribution directory and zip it into a
deployment bundle:

```
cp index.py dist

pushd dist
zip -r /tmp/cloudtrail-lambda.zip .
popd
```


## Deploying

The deployment process requires multiple steps:

1. Create the Elasticsearch cluster and a dummy Lambda using the [CloudFormation template](cloudformation.yml).
   This template requires the following parameters:

    * `LambdaName`:
      The name of the Lambda function. This is also used for the function's execution role.
    * `CloudTrailBucket`:
      The name of the S3 bucket where CloudTrail is saving event logs.
    * `CloudTrailKey`:
      The prefix within this bucket for the log files, if used. You must include the trailing
      slash on this value.
    * `ElasticsearchDomainName`:
      The domain name for the Elasticsearch cluster. This must comply with DNS naming rules
      (ie, lowercase and with hyphens but no underscores).
    * `ElasticsearchInstanceType`:
      The type of instance to use for the Elasticsearch cluster. The default is `t2.medium.elasticsearch`,
      which will be sufficient for a relatively low-volume environment.
    * `ElasticsearchStorageSize`:
      The size of the storage volume, in gigabytes. The maximum size depends on the selected
      instance type; the default is 32.
    * `AllowedIPs`:
      Used to construct a permissions policy for the Elasticsearch cluster that allows access
      from browsers. You should specify the public IP address of your local network, which you
      can find by Googleing for "what's my IP". If you have multiple public IP addresses, list
      them all, separated by a comma.

   Note: if you already have an Elasticsearch cluster, feel free to delete that section of the
   template. However, you will have to update all references to `ElasticSearchDomain` elsewhere
   in the stack, replacing them with your cluster's endpoint and ARN.

2. Upload the distribution bundle for the Lambda function.

   The function created by the CloudFormation template has dummy content; when invoked, it will
   tell you to upload the real function. I find this easier to manage for one-off Lambdas than
   the "standard" process of first uploading the function bundle to S3 then telling CloudFormation
   where to find it.

   This step is simply a matter of going to the Lambda function definition in the AWS Console,
   scrolling down to the "Code entry type" drop-down, changing it to "Upload a .zip file", and
   then uploading the file that you created earlier.

3. Create the event trigger.

   CloudFormation doesn't provide a way to configure bucket notifications separately from bucket
   creation. Since this post is about uploading CloudTrail events to Elasticsearch, and not about
   configuring CloudTrail, I'm leaving this as a manual step.

   This is also managed from the Lambda function definition. Click the "Add trigger" button,
   select S3 as the trigger type, leave the event type as "All object create events", and select
   the bucket and prefix that holds your CloudTrail logs.

Within a few minutes, you should be able to go to the Elasticsearch cluster and see a new
index named "cloudtrail-YY-MM-DD" (where YY-MM-DD refers to the current date). You can then
configure this index in Kibana, and start to explore your API events.



## Warnings and Caveats

You will incur charges for the Elasticsearch cluster and Lambda invocations. The default cluster
in the CloudFormation template is `t2.medium.elasticsearch`, which costs $1.75 per day (plus
storage charges of $0.32/month).

Elasticsearch does not clean up its indexes by default. You can use the cleanup Lambda described
[here](https://github.com/kdgregory/aws-misc/tree/master/lambda/es-cleanup-signed) to maintain a
constant number of days worth of indexes (the upload Lambda creates one index per day). How many
indexes you can support will depend on your API volume and the size of the cluster.

Deleting the Lambda function -- either manually or by deleting the CloudFormation stack -- does
_not_ delete the event trigger. You must explicitly delete it by going to the S3 bucket, clicking
"Events" under the "Properties" tab, and then deleting the notification.
