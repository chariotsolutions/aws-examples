This is a Lambda that processes CloudTrail log files from S3 and writes the events
to an OpenSearch/Elasticsearch cluster.


# Warnings and Caveats

**This version of the program works with Amazon OpenSearch, or Elasticsearch versions
7.x and above**.  Version 7 [introduced a breaking change](https://www.elastic.co/guide/en/elasticsearch/reference/7.0/removal-of-types.html),
in which it no longer supports defining mapping types when creating an index.

**You will incur charges for the OpenSearch cluster and Lambda invocations**,
as well as for S3 storage of the raw CloudTrail events. The provided CloudFormation
template creates a stack using a single `t3.small.search` instance and 64 GB of disk.
This costs approximately $34/month in US zones.

**Amazon OpenSearch does not automatically clean up its indexes**. You can
use an [Index State Management](https://docs.aws.amazon.com/opensearch-service/latest/developerguide/ism.html)
Policy to delete old indexes, or manually delete them with an HTTP `DELETE` request.
As configured, the Lambda creates one index for each month of data. How many indexes
you can support will depend on your AWS API volume and the size of the cluster.

**Deleting the Lambda function -- either manually or by deleting the CloudFormation
stack -- does _not_ delete the event trigger**. You must explicitly delete it by going
to the S3 bucket holding your CloudTrail events, clicking "Events" under the "Properties"
tab, and then removing the notification.


# Building and Deploying

This project consists of a single Lambda, written in Python. It has multiple modules,
and uses the third-party [`requests`](https://pypi.org/project/requests/) and
[`aws-requests-auth`](https://pypi.org/project/aws-requests-auth/) libraries to access
OpenSearch.

The easiest way to build is with `make`, and there are two Makefiles:

* `Makefile.pip` uses `pip` to install the external dependencies.

* `Makefile.poetry` uses [Poetry](https://python-poetry.org/) for dependency management.
  In my opinion Poetry is preferable to `pip` because it also provides a virtual environment
  for running tests or the REPL.

Both Makefiles provide the following targets (the first four are shown in dependency order,
the last two are independent):

* `init` installs the third-party libraries.

* `test` runs tests. At this time there are only a few tests, intended to demonstrate the
  build process rather than exercise the code.

* `package` creates the Lambda deployment bundle

* `deploy` uses the AWS CLI to upload the Lambda deployment bundle.

* `quicktest` runs tests without invoking the `init` dependency. This allows fast turnaround
  when you're actively modifying the code.

* `clean` deletes the deployment bundle and all working directories. It does _not_ delete the
  Poetry virtual environment.

Deploying is a multi-step process:

1. [Enable CloudTrail](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-create-and-update-a-trail.html)

   For this example, I'm going to assume that you already have CloudTrail enabled,
   and an S3 bucket configured to accept its output. While it would simplify the
   example if my CloudFormation script created the trail and bucket, it would put
   me in the position of either delivering an insecure and incomplete solution, or
   one that could not easily be torn down.

   Here are some things to consider when creating your own trail:

   * Use a dedicated bucket.

   * Use server-side encryption on this bucket.

   * Enable [Object Lock](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock.html)
     on that bucket, to ensure that an intruder can't delete the events that show their activity.
     When you turn on object lock, you need to pick a retention mode and period. I recommend 90
     days for the retention period, and "compliance" mode for the retention type.

     **Beware:** compliance mode means that you _can not delete the object_ until the retention
     period expires. This is good from a security perspective, but bad from a cost perspective
     if you pick an over-long period.

   * Create a cross-region trail. By default, CloudTrail only records events from the _current_ region.
     You want to capture _all_ of the events for your account.

   * If you're in an organization, create the bucket and trail in the organization root account, and
     enable for all child accounts.

2. Create the OpenSearch cluster and Lambda

   The [provided CloudFormation template](cloudformation.yml) creates an Amazon OpenSearch cluster
   and Lambda outside a VPC. This template has several parameters, most of which are optional:

    * `LambdaName`:
      (optional) The name of the Lambda function. This is also used to name the function's
      execution role. Default: `CloudTrail_to_OpenSearch`.

    * `CloudTrailBucket`:
      The name of the S3 bucket where CloudTrail is saving event logs. No default.

    * `CloudTrailPrefix`:
      (optional) The prefix within this bucket for the log files. Yes, this goes against my
      recommendation above for a dedicated bucket, but the real world sometimes has different
      ideas. If used, you must include the trailing slash on this value (eg, "cloudtrail/",
      not "cloudtrail").

    * `OpenSearchDomainName`:
      (optional) The domain name for the OpenSearch cluster. This must comply with DNS naming
      rules (ie, lowercase and with hyphens but no underscores). Default: `cloudtrail-events`.

    * `OpenSearchInstanceType`:
      (optional) The type of instance to use for the OpenSearch cluster. The default is
      `t3.small.search`, which is sufficient for a few million events per month, but will
      need to be increased if you're in a high-activity organization.

    * `OpenSearchStorageType`:
      The type of storage volume. This defaults to `gp3`, which gives a reasonable baseline
      performance. The only reason that this is exposed as a parementer is that some instance
      types do not support all storage types.

    * `OpenSearchStorageSize`:
      (optional) The size of the storage volume, in gigabytes. The maximum size depends on the
      selected instance type; the default is 64.
      
    * `AllowedIPs`:
      (optional) Used to construct a permissions policy for the OpenSearch cluster that allows
      access from browsers. You should specify the public IP address of your local network,
      which you can find by Googleing for "what's my IP". If you have multiple public IP
      addresses, list them all, separated by a comma. No default.

2. Build and deploy the Lambda.

   One of the annoying things about CloudFormation is that the `AWS::Lambda::Function` resource
   can either specify the Lambda deployment as 4k of literal text (confusingly named `ZipFile`)
   or as a reference to a deployment bundle stored on S3. There's no way to deploy a local file.
   As a result, I use a hack: the CloudFormation template deploys a dummy Lambda, which you must
   then replace.

   You can build and deploy the Lambda this in one step using `make` (changing to `Makefile.pip`
   if that's your preference):

   ```
   make -f Makefile.poetry deploy
   ```
   
   If you changed the `LambdaName` parameter when creating your stack, you'll need to pass the
   new name to the `deploy` target:

   ```
   make -f Makefile.poetry deploy LAMBDA_NAME=MyFunctionName
   ```

3. Create the event trigger.

   CloudFormation requires you to configure bucket notifications at the time you create the bucket.
   Since this post is about uploading CloudTrail events to OpenSearch, and not about configuring
   CloudTrail, I'm leaving this as a manual step:

   1. Open the Lambda function in the Console. 
   2. Click the "Add trigger" button. 
   3. Select S3 as the trigger type. 
   4. Leave the event type as "All object create events".
   5. Pick the bucket that you configured with CloudTrail, and enter the log prefix (if any).
   6. Click the checkbox that says you understand that writing back to the bucket from Lambda
      is a Bad Idea (this Lambda doesn't do it).
   7. Click "Add"

   Within a few minutes, you should be able to go to the OpenSearch cluster and see a new
   index named "cloudtrail-YYYY-MM" (where YYYY-MM is the current year and month). You can then
   configure this index in Kibana, and start to explore your API events.

4. Configure Kibana

   Before using Kibana, you must [create an index pattern](https://www.elastic.co/guide/en/kibana/current/index-patterns.html).
   For indexes generated by this project, the pattern name should be `cloudtrail-*`, and the
   time filter field should be `eventTime`.


# Bulk Upload

If you already had CloudTrail enabled, then you can use a bulk upload process to load
all existing events into your cluster (this will be much faster and easier than trying
to trigger the Lambda).

From within the project directory:

1. Install all of the dependencies. You can use either of the Makefiles to do this.

2. Set the necessary environment variables:

    * `ES_HOSTNAME`: the hostname of the OpenSearch cluster
    * `AWS_ACCESS_KEY_ID`: your AWS access key
    * `AWS_SECRET_ACCESS_KEY`: your AWS secret key
    * `AWS_SESSION_TOKEN` if you have assumed a role (eg, from using IAM Identity Center
      to get credentials).
    * `AWS_REGION`: region where the OpenSearch cluster resides

    Note 1: the AWS keys are used to explicitly authorize the OpenSearch HTTPS requests,
    so you can't use a configured profile.

    Note 2: the provided AWS credentials must have the `es:ESHttpGet`, `es:ESHttpPost`, and
    `es:ESHttpPut` permissions on the OpenSearch cluster.

3. Run the program:

    ```
    PYTHONPATH=`pwd`/build python -m cloudtrail_to_elasticsearch.bulk_upload --dates 2022-04-01 2022-04-30 --s3 BUCKET_NAME CLOUDTRAIL_PREFIX
    ```

    The `PYTHONPATH` configuration makes your dependencies available (if you're using Poetry,
    you could alternatively use `poetry run`).

    The `--dates` option specifies a starting and ending date; you should start with the
    date of the first CloudTrail events loaded to your S3 bucket, and end with the current
    date. Updates are idempotent, so you can (and should) overlap with any events that are
    already in OpenSearch. If you don't specify this parameter, the program will load
    all events in your bucket -- which may take quite some time.

    The `--s3` option tells the program to read from an S3 bucket and prefix; replace the
    values shown here with those for your installation. 

    If you've downloaded events, you can instead use the option `--local` with the path of
    your download directory, and the program will read event files from there.

Assuming that you've done everything right, you should see a series of "processing"
messages that let you know what file is being processed, interspersed with "writing
events" messages that tell you how many events have been written in each batch. The
number of files may be quite long; I recommend using the `tee` program and saving
the output to a file to make sure there are no errors.



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

My solution is to "flatten" the `requestParameters`, `responseElements`, and `resources` sub-objects
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
and [dynamic templates](https://www.elastic.co/guide/en/elasticsearch/reference/7.0/dynamic-templates.html)
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

The Lambda also configures some basic index settings:

  * `'index.mapping.total_fields.limit': 8192`

    One thing that I learned early-on is that there are a lot of different field
    names in CloudTrail, and that the default value of 1,000 for this setting is
    way too low. Across all indexes, we currenty have 4,695 distinct field names;
    you may have more or fewer based on the services that you use.

  * `'index.number_of_shards': 1`

    Sizing of Elasticsearch indexes, including picking the number of shards for an
    index, is somehing of a [dark art](https://www.elastic.co/guide/en/elasticsearch/reference/current/size-your-shards.html).
    However, if you're using the default CloudFormation template in this project,
    it doesn't make sense to have more than one shard per index, because all of
    them will live on a single node.

    If you have sufficient CloudTrail volume that you require more than one node to
    store the events, then I recommend picking a number of shards equal to the
    number of nodes. The reasoning for this is that most of your queries will be
    against relatively recent data, so you will get a bigger benefit from running
    those queries on all nodes.

  * `'index.number_of_replicas': 0`

    By default, AWS Opensearch creates indexes with replicas. On a single-node
    cluster there's no place for those replicas to go. And given that the raw
    event data is stored in S3, I think that there's little need to replicas in
    any case. That will, of course, mean some amount of downtime if your cluster
    ever fails, while you repopulate a new cluster.

One last thing about index creation: the code will check to see if the index exists before
trying to create it. That works great during "normal" operation, in which CloudTrail delivers
one file at a time to S3. However, if you upload a large number of files at once, Lambda will
scale up the number of executing functions to match the number of files, and this can cause a
race condition between creation and use that results in an error.

To solve this, I recommend setting reserved concurrency on the Lambda to 1, which will prevent
concurrent executions. If you have a large number of CloudTrail files that already live on S3,
Ir recommend using a [bulk upload](#bulk-upload).


## Index names

As noted above, we create one index per month, but how do we give the index a relevant name?

The optimal way would be to base the index name on the timestamp of the events it contains.
Unfortunately, the files that we receive from S3 may contain events from different days, so
it would increase the complexity of the code if we had to split each file into multiple
uploads.

So instead, we extract the year and month from the key that CloudTrail uses to write the
event file. This is extracted via regular expression.
