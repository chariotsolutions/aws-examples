This is a Lambda that processes CloudTrail log files from S3 and writes the events
into an Elasticsearch cluster.


# Warnings and Caveats

You will incur charges for the Elasticsearch cluster and Lambda invocations, as well
as for S3 storage of the raw CloudTrail events. The provided CloudFormation template
creates a stack using a single `t2.medium.elasticsearch` instance and 32 GB of disk. 
This costs $1.75 per day plus storage charges of $0.32/month.

AWS Managed Elasticsearch does not automatically clean up its indexes. You can use the
cleanup Lambda [here](https://github.com/kdgregory/aws-misc/tree/master/lambda/es-cleanup-signed)
to maintain a constant number of indexes. As configured, the Lambda creates one index
for each month of data.  How many indexes you can support will depend on your AWS API
volume and the size of the cluster.

Deleting the Lambda function -- either manually or by deleting the CloudFormation stack --
does _not_ delete the event trigger. You must explicitly delete it by going to the S3
bucket, clicking "Events" under the "Properties" tab, and then deleting the notification.


# Building and Deploying

This project consists of a single Lambda, written in Python. It has multiple modules,
and uses the third-party [`requests`](https://pypi.org/project/requests/) and
[`aws-requests-auth`](https://pypi.org/project/aws-requests-auth/) libraries to access
Elasticsearch.

The easiest way to build is with `make`, and there are two Makefiles:

* `Makefile.pip` uses `pip` to install the external dependencies.

* `Makefile.poetry` uses [Poetry](https://python-poetry.org/) for dependency management.
  In my opinion Poetry is preferable to `pip` because it also provides a virtual environment
  for running tests or the REPL.

Other than the way that these Makefiles manage dependencies they are identical, and provide
the following targets (the first four are shown in dependency order; the last two do not
have dependencies):

* `init` installs the third-party libraries.

* `test` runs tests. At this time the tests are minimal, intended to demonstrate the build
  process rather than exercise the code.

* `package` creates the Lambda deployment bundle

* `deploy` uses the AWS CLI to upload the Lambda deployment bundle.

* `quicktest` runs tests without invoking the `init` dependency. This allows fast turnaround
  time when you are actively modifying the code.

* `clean` deletes the deployment bundle and all working directories. It does _not_ delete the
  Poetry virtual environment.

Deploying is a multi-step process:

1. Enable CloudTrail.

   For this example, I'm going to assume that you already have CloudTrail enabled,
   and an S3 bucket configured to accept its output. While it would simplify the
   example if my CloudFormation script created the trail and bucket, it would put
   me in the position of either delivering an insecure and incomplete solution, or
   one that could not easily be torn down.

   Here are some things to consider when creating your own trail:

   * Use a dedicated bucket.

   * Use server-side encryption on this bucket.

   * Enable [Object Lock](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock.html)
     on that bucket, to ensure that an intruder can't delete the trails that show their activity.
     Note that there are two type of Object Lock, and the "governance mode" locks can be overridden.
     To ensure that an attacker cannot delete CloudTrail logs, you need to use a "legal hold," which
     does not permit _any_ deletion of an object within its retention period (as such, you may want
     to limit the retention period, especially if this is the first time that you've set up CloudTrail).

   * Create a cross-region trail. By default, CloudTrail only records events from the _current_ region.
     You want to capture _all_ of the events for your account.

   * If you're in an organization, create the bucket and trail in the organization root account, and
     enable for all child accounts.

2. Create the Elasticsearch cluster and Lambda

   The [provided CloudFormation template](cloudformation.yml) will create the Elasticsearch cluster
   and Lambda outside a VPC. This template has several parameters, most of which are optional:

    * `LambdaName`:
      (optional) The name of the Lambda function. This is also used to name the function's
      execution role. Default: `CloudTrail_to_Elasticsearch`.

    * `CloudTrailBucket`:
      The name of the S3 bucket where CloudTrail is saving event logs. No default.

    * `CloudTrailPrefix`:
      (optional) The prefix within this bucket for the log files. Yes, this goes against my
      recommendation above for a dedicated bucket, but the real world sometimes has different
      ideas. If used, you must include the trailing slash on this value (eg, "cloudtrail/",
      not "cloudtrail").

    * `ElasticsearchDomainName`:
      (optional) The domain name for the Elasticsearch cluster. This must comply with DNS naming
      rules (ie, lowercase and with hyphens but no underscores). Default: `cloudtrail-events`.

    * `ElasticsearchInstanceType`:
      (optional) The type of instance to use for the Elasticsearch cluster. The default is
      `t2.medium.elasticsearch`, which is sufficient for a few million events per month, but
      may need to be increased if you're in a high-activity organization.

    * `ElasticsearchStorageSize`:
      (optional) The size of the storage volume, in gigabytes. The maximum size depends on the
      selected instance type; the default is 32.
      
    * `AllowedIPs`:
      (optional) Used to construct a permissions policy for the Elasticsearch cluster that
      allows access from browsers. You should specify the public IP address of your local
      network, which you can find by Googleing for "what's my IP". If you have multiple public
      IP addresses, list them all, separated by a comma. No default.

   One of the annoying things about CloudFormation is that the `AWS::Lambda::Function` resource
   can either specify the Lambda deployment as 4k of literal text (confusingly named `ZipFile`)
   or as a reference to a deployment bundle stored on S3. There's no way to deploy a local file.
   As a result, I use a hack: the CloudFormation template deploys a dummy Lambda, which you must
   replace in the next step.

2. Build and deploy the Lambda.

   As noted above, you can build and deploy the Lambda via `make`. Here I use the Poetry version
   of the Makefile:

   ```
   make -f Makefile.poetry deploy
   ```
   
   If you changed the `LambdaName` parameter when creating your stack, you'll need to pass the
   new name to the `deploy` target:

   ```
   make -f Makefile.poetry deploy LAMBDA_NAME=MyFunctionName
   ```

3. Create the event trigger.

   CloudFormation doesn't provide a way to configure bucket notifications separately from bucket
   creation. Since this post is about uploading CloudTrail events to Elasticsearch, and not about
   configuring CloudTrail, I'm leaving this as a manual step.

   To do this, open the Lambda function in the Console. Click the "Add trigger" button, select S3
   as the trigger type, leave the event type as "All object create events", and select the bucket
   and prefix that holds your CloudTrail logs.

   Within a few minutes, you should be able to go to the Elasticsearch cluster and see a new
   index named "cloudtrail-YYYY-MM" (where YYYY-MM is the current year and month). You can then
   configure this index in Kibana, and start to explore your API events.

4. Configure Kibana

   Before using Kibana, you must [create an index pattern](https://www.elastic.co/guide/en/kibana/current/index-patterns.html).
   For indexes generated by this project, the pattern name should be `cloudtrail-*`, and the
   time filter field should be `eventTime`.


# Implementation Notes

## Event transformation

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
array of objects, one per instance created. The CloudTrail event looks like this (showing only the
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


## Elasticsearch index creation

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

One last thing about index creation: the code will check to see if the index exists before
trying to create it. That works great during "normal" operation, in which CloudTrail delivers
one file at a time to S3.

However, if you upload a large number of files at once, Lambda will scale up the number of
executing functions to match the number of files, and this can cause a race condition between
creation and use. With the end result that some Lambda invocations fail and are not retried.

If you are doing a bulk upload, I recommend setting the reserved concurrency on the Lambda to
1, which will prevent concurrent executions.


## Index names

As noted above, we create one index per month, but how do we give the index a relevant name?

The optimal way would be to base the index name on the timestamp of the events it contains.
Unfortunately, the files that we receive from S3 may contain events from different days, so
it would increase the complexity of the processor if we had to split each file into multiple
uploads.

So instead, we use a hack: CloudTrail writes files using a very long key that includes the
account number, region, and date. For example:

```
AWSLogs/o-xf2e8q7b2u/123456789012/CloudTrail/us-east-1/2020/03/06/123456789012_CloudTrail_us-east-1_20200306T1740Z_8hgMvcKamTPw3TTO.json.gz
```

To create the index name, we use a regular expresion to extract components from the final
datestamp (`20200306T1740Z`) and translate to an index name: `cloudtrail-2020-03`.


# Uploading old events

The Lambda responds to new files arriving on S3. If you had CloudTrail enabled, you'll already
have events stored on S3. To load these files into Elasticsearch, you can invoke the loader from
the command line.

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
