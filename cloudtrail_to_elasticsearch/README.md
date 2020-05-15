This is a Lambda that will process CloudTrail log files from S3 and write the events
into an Elasticsearch cluster, where they can easily be explored (unlike, when using
tools such as AWS Athena).


# Warnings and Caveats

You will incur charges for the Elasticsearch cluster and Lambda invocations, as well as
for S3 storage of the raw CloudTrail events.. The provided CloudFormation template
creates a stack using a single `t2.medium.elasticsearch` instance and 32 GB of disk. 
This costs $1.75 per day plus storage charges of $0.32/month.

Elasticsearch does not automatically clean up its indexes. You can use the cleanup Lambda
described [here](https://github.com/kdgregory/aws-misc/tree/master/lambda/es-cleanup-signed)
to maintain a constant number of indexes. As configured, the Lambda creates one index for
each month of data.  How many indexes you can support will depend on your API volume and the
size of the cluster.

Deleting the Lambda function -- either manually or by deleting the CloudFormation stack --
does _not_ delete the event trigger. You must explicitly delete it by going to the S3
bucket, clicking "Events" under the "Properties" tab, and then deleting the notification.


# Implementation Notes

Before we get into deploying the Lambda, here are a few of the constraints that went into its
design.


## Event Transformation

The big challenge with storing CloudTrail events in Elasticsearch is that the events have a large
variety of sub-objects, with arbitrary nesting. The `requestParameters` and `responseElements`
sub-objects are a particular challenge: not only are there a lot of distinct fields in these
objects (causing what the Elastic docs call a "mapping explosion"), but they also contain arrays
of objects, which [Elasticsearch doesn't handle well](https://www.elastic.co/guide/en/elasticsearch/reference/current/array.html)
(in my experience, it gives up and leaves the sub-object unindexed).

While the Lambda could explicitly transform each event into a standard format, that would be an
endless task: AWS constantly adds new API calls. Moreover, dynamic mapping is one of Elasticsearch's
strengths; we should use it.

My solution was to "flatten" the `requestParameters`, `responseElements`, and `resources` sub-objects
before writing the event. This is best explained by example: the `RunInstances` API call returns an
array of objects, one per isntance created. The CloudTrail event looks like this (showing only the
fields relevant to this example):

```
{
    "eventID": "8d483369-df03-4497-a339-963fb9e1cb40",
    "eventName": "RunInstances",
    "eventTime": "2020-01-03T14:41:10Z",
    "awsRegion": "us-west-2",
    "userIdentity": {
        ...
    },
    "requestParameters": {
        ...
    },
    "responseElements": {
        "instancesSet": {
            "reservationId": "r-06faea10dec62634f",
            "items": [{
                "instanceId": "i-0a7badded743619b6",
                "placement": {
                    "availabilityZone": "us-west-2a",
                    "tenancy": "default"
                },
                ...
            }]
        }
        ...
    },
    ...
}
```

"Flattening" the event transforms the `responseElements` child object into this:

```
"responseElements_flattened": {
    "reservationId": [ "r-06faea10dec62634f" ],
    "instanceId": [ "i-0a7badded743619b6" ],
    "availabilityZone": [ "us-west-2a" ],
    "tenancy": [ "default" ]
    ...
```

There are a few things to notice: first, the `instancesSet`, `items`, and `placement` keys have
disappeared entirely, as they weren't leaf keys. Second is that each sub-key references an
array of values. Lastly, all of those values are strings, even if the source value was a
number (unfortunately, Elasticsearch sometimes tries to be smart about parsing strings,
which causes an occasional field conflict; see [below](#elasticsearch-index-creation)).

In my opinion, this transformation is easier to use than one that attempts to maintain
the hierarchical structure: if I need to find the `RunInstances` event that created an
instance, I don't want to remember the specific hierarchy of field names where that
event holds an instance ID, I just want to filter on `instanceId`. This format does,
however, lead to some strangeness: for example, the `RunInstances` event has an
`instanceState.code` value and a `stateReason.code` value; both are flattened into
`code`, and the former is converted to a string.

> Note: the non-open-source version of Elasticsearch provides
  [flattened fields](https://www.elastic.co/guide/en/elasticsearch/reference/master/flattened.html).
  If you are self-hosting, and are willing to pre-create your mappings, you could
  take advantage of them.

Lastly, the transformation preserves the "raw" values of these fields as JSON strings,
using the keys `requestParameters_raw`, `responseElements_raw`, and `resources_raw`.
You can use these fields to identify specific hierarchical values, and they're also
indexed as free-form text.


## Elasticsearch Index Creation

As I mentioned earlier, we rely on dynamic mapping to handle the wide variety of fields
in a CloudTrail event. However, this can cause Elasticsearch to make the wrong choice
for field type. For example, if it sees something that it can parse as a date, it will
chose the `date` field type. If it later sees something in that field that _can't_ be
parsed as a date, it will reject the record.

The `apiVersion` field behaves just this way: its values actually represent dates, but
different services use different formats. The "flattened" fields described above are
another case: even though I write them into the JSON as strings, they sometimes get parsed
as something else.

The solution to these problems is to make some explicit mapping decisions when creating
the index -- and to _explicitly_ create it, rather than let Elasticsearch create it the
first time you try to write data.

Here is the default mapping that we use, which specifies an explicit mapping for `apiVersion`
and [dynamic templates](https://www.elastic.co/guide/en/elasticsearch/reference/6.8/dynamic-templates.html)
for the various "flattened" fields. These dynamic templates tell Elasticsearch that any
fields that match the pattern should be indexed as text, regardless of what it thinks
they should be.

```
'mappings': {
    'cloudtrail_event': {
        'dynamic_templates': [
            {
                'flattened_requestParameters': {
                        'path_match': 'requestParameters_flattened.*',
                        'mapping': { 'type': 'text' }
                }
            }, {
                'flattened_responseElements': {
                        'path_match': 'responseElements_flattened.*',
                        'mapping': { 'type': 'text' }
                }
            }, {
                'flattened_resources': {
                        'path_match': 'resources_flattened.*',
                        'mapping': { 'type': 'text' }
                }
            }
        ],
        'properties': {
            'apiVersion': { 'type': 'text' }
        }
    }
}
```

There's one more thing to configure: the maximum number of allowed fields. This is
far beyond what we've seen in our environment, but I went through several iterations
of "oops, that wasn't enough." This is also configured by the Lambda when creating a
new index:

```
'settings': {
    'index.mapping.total_fields.limit': 8192
}
```

There are two additional settings that I haven't put into the code: number of shards
per index and number of replicas per shard. With AWS Managed Elasticsearch 6.8, each
index defaults to five shards, and one replica per shard. Unless you have enormouse
volume, this is far too many shards: for time-series data (which logs are), Elastic
recommends [20-40 GB per shard](https://www.elastic.co/blog/how-many-shards-should-i-have-in-my-elasticsearch-cluster).

We've found that 1,000,000 CloudTrail events translates into approximately 1.2 GB,
and our monthly usage is lower than that, so there's no reason for multiple shards.
Moreover, our cluster runs on a single node (rather than pay for an extra node,
we're willing to recover from snapshot if the cluser goes south). This means that
there's no reason for shard replicas, as they won't be assigned to a node.

If you are in a similar situation, edit the default index configuration (in
`processor.py`), changing the settings to look like this:

```
'settings': {
    'index.mapping.total_fields.limit': 8192,
    'index.number_of_shards': 1,
    'index.number_of_replicas': 0
}
```


# Building

This project consists of a single Lambda, written in Python, using the
[`requests`](https://pypi.org/project/requests/) and
[`aws-requests-auth`](https://pypi.org/project/aws-requests-auth/)
libraries to write to Elasticsearch (it was adapted from prior work; I might rewrite
using the Elasticsearch Python libraries, but this is a low-priority task).

To produce the deployment bundle for Lambda, you need to combine the source code (found
in the `src` directory) with the libraries. Rather than use a virtual environment, I
just install the libraries using `pip` (note: `--system` is only required for Ubuntu,
which otherwise ignores the `--target` option, and you can omit `boto3` if you're
just planning to upload to Lambda):

```
pip3 install --system --target lib boto3 requests aws-requests-auth
```

To build the deployment bundle, you need to produce a ZIP file that combines the
`src` and `lib` directories. Here are the commands for Linux:

```
rm /tmp/cloudtrail-lambda.zip

pushd src
zip /tmp/cloudtrail-lambda.zip *.py
popd

pushd lib/python3.*/site-packages
zip -r /tmp/cloudtrail-lambda.zip *
popd
```


## Deploying

Deployment is a multi-step process:

1. Create the Elasticsearch cluster and a dummy Lambda using the [CloudFormation template](cloudformation.yml).
   This template requires the following parameters:

    * `LambdaName`:
      The name of the Lambda function. This is also used to name the function's execution role.
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
      which is sufficient for a few million events per month, but may need to be increased
      if you're in a high-activity organization.
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

2. Create and upload the distribution bundle for the Lambda function.

   To simplify the CloudFormation template, I created a dummy function; when invoked, it will tell
   you to upload the real function. I find this easier to manage for one-off Lambdas than the
   "standard" process of first uploading the function bundle to S3 theand n telling CloudFormation
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
index named "cloudtrail-YYYY-MM" (where YYYY-MM is the current year and month). You can then
configure this index in Kibana, and start to explore your API events.


# Configuring Kibana

Before using Kibana, you must [create an index pattern](https://www.elastic.co/guide/en/kibana/current/index-patterns.html).
For indexes generated by this project, the pattern name should be `cloudtrail-*`, and the
time filter field should be `eventTime`.


# Running on the command-line

If you've had CloudTrail enabled, you'll already have events stored on S3. To load these files
into Elasticsearch, you can invoke the loader from the command line.

First, however, you need to set environment variables:

* `ES_HOSTNAME`: the hostname of the Elasticsearch cluster
* `AWS_ACCESS_KEY_ID`: AWS access key
* `AWS_SECRET_ACCESS_KEY`: AWS secret key
* `AWS_REGION`: region where the Elasticsearch cluster resides

Then, run the bulk upload module to read all files from S3 with a given prefix (if you don't
use a prefix to segregate CloudTrail from other log output, you can always use `cloudtrail`,
which is the start of the AWS-defined prefix). The events are uploaded into monthly indexes,
using the file's datestamp.

```
src/bulk_upload.py BUCKET_NAME PREFIX
```

Note that Elasticsearch updates are idempotent, based on the CloudTrail event ID, so you can run
the upload scripts as many times as you'd like (you will, however, be charged for data transfer).
