This project contains CloudFormation templates to create Amazon Data Firehoses that write
CloudTrail events to different destinations:

* [firehose-parquet.yml](firehose-parquet.yml) writes to a Parquet table stored on S3 and
  managed by Glue.
* [firehose-iceberg.yml](firehose-iceberg.yml) writes to an Iceberg table stored on S3 and
  managed by Glue.
* [firehose-s3table.yml](firehose-s3table.yml) writes to a table managed by an S3 Table
  Bucket (with LakeFormation granting access).
* [firehose-redshift.yml](firehose-redshift.yml) writes to a table managed by Redshift.


## Deployment

### Prerequisites

You must have an existing Kinesis Data Stream that receives CloudTrail events as stringified
JSON. [This project](../cloudtrail_to_kinesis) will deploy a stream, along with a Lambda that
listens for notifications on the S3 bucket that contains your trail (or let you populate the
stream manually from CloudTrail files).

### Transformation Lambda

Each of these Firehoses uses a transformation Lambda to (1) convert field names from the
camelCase originals, and (2) stringify any nested objects. To avoid duplicating code, the
CloudFormation templates create a dummy Lambda that raises an exception (so the Firehose
won't attempt to process the records). After deploying the Firehose, you must update the
Lambda's source code from [this file](../cloudtrail_firehose_transform/index.py).

### Common Parameters

The following parameters are common to all templates:

* `KinesisStream`: the stream where source events are written. Defaults to `cloudtrail_events`.
* `FirehoseErrorBucket: the S3 bucket where Firehose will write any errors. No default.
* `FirehoseErrorPrefix: initial prefix for errors written by Firehose, the table name will be
  appended to this value. Defaults to `firehose_errors/`.
  followed by the destination name (eg, `firehose_errors/cloudtrail_iceberg/`).
* `FirehoseBatchSize`: specifies the desired size of output files. Default depends on destination.
* `FirehoseBatchTime`: specifies how long Firehose will aggregate data before writing a file. The
  default is 900 seconds, which is reasonable for an actual deployment, but too high for development;
  change to 60 seconds so that you have a fast feedback loop.

There are other parameters that are specific to the template (although they may be shared between
two or more), and are documented with their template.


### firehose-parquet.yml

This template creates a Firehose that writes Parquet files to an S3 location, along with a Glue
table that can be used to read that data.

Parameters:

* `GlueDatabase`: the name of an existing Glue database where the table definition is created.
  Defaults to `default`.
* `TableName`: the name of the tble to create. This will also be used as the prefix for the
  table's data files. Defaults to `cloudtrail_parquet`.
* `TableBucket`: the name of an existing S3 bucket that will hold the table's data.

Notes:

* The data produced by this Firehose may contain duplicate events, either due to CloudTrail
  recording those duplicates, or best-effort handling of CloudTrail notifications.

* Deleting this stack _does not_ delete the data. If you delete and then recreate the stack,
  you will already have data in the table.


### firehose-iceberg.yml

This template creates a Firehose that writes Iceberg files to an S3 location, along with a Glue
table that can be used to read that data.

Parameters:

* `GlueDatabase`: the name of an existing Glue database where the table definition is created.
  Defaults to `default`.
* `TableName`: the name of the tble to create. This will also be used as the prefix for the
  table's data files. Defaults to `cloudtrail_parquet`.
* `TableBucket`: the name of an existing S3 bucket that will hold the table's data.
* `PrimaryKey`: the column used as a primary key for the table, allowing upserts. Defaults to
  `event_id`, and should not be changed.


Notes:

* The Iceberg template does not configure table optimizations. As-of this writing, the only optimization
  that CloudFormation supports is compaction, and creating that optimization in the same template as the
  table causes CloudFormation to fail. However, this emplate does create (and output) a role that Glue can
  use to perform optimizations.

* Deleting this stack _does not_ delete the data. If you delete and then attempt to recreate the stack,
  it will fail due to existing metadata.


### firehose-s3tables.yml

This template creates an S3 table bucket, namespace, and table, along with a Firehose to populate it.

This template must be run in two phases: as of this writing, you cannot assign LakeFormation permissions
using CloudFormation: the `AWS::LakeFormation::PrincipalPermissions` only accepts account numbers as a
catalog ID. To work-around, you must do the following:

* Apply the template with whatever configuration is appropriate for your environment, _leaving
  the `Phase` parameter with its default value of "1"_.
* Go into LakeFormation, and attach permissions to the created Firehose Role, as described
  [here](https://docs.aws.amazon.com/AmazonS3/latest/userguide/grant-permissions-tables.html).
  Firehose requires Describe permission on `s3tablescatalog` and the catalog created by this
  template, and Super permissions on the table.
* Re-apply the template, with `Phase` set to "2".


Parameters:

* `Phase`: used to defer creation of Firehose until permissions have been configured (see notes).
* `TableBucketName`: the name of the table bucket to create. Defaults to `example`.
* `NamespaceName`: the name of the namespace to create. Defaults to `default`.
* `TableName`: the name of the tble to create. This will also be used as the prefix for the
  table's data files. Defaults to `cloudtrail`.
* `PrimaryKey`: the column used as a primary key for the table, allowing upserts. Defaults to
  `event_id`, and should not be changed.

Notes:

* When you delete this stack, it will delete the table bucket, but the actual bucket deletion
  happens asynchronously. This means that the name can not be reused right away (I have seen
  reports that it might take a day or more before the name can be reused).

* When you delete this stack, you must manually revoke the LakeFormation permissions that you
  granted to the Firehose execution role.


### firehose-redshift.yml
