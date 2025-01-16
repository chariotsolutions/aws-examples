This project contains CloudFormation templates for the blog post [Populating Iceberg Tables
with Amazon Data Firehose](https://chariotsolutions.com/blog/post/firehose_iceberg/).

Both templates create a Kinesis Firehose fed from a pre-existing Kinesis Data Stream, along with a
Glue table to receive data from that Firehose. The first, [firehose-parquet.yml](firehose-parquet.yml),
writes the records as Parquet; the second, [firehose-iceberg.yml](firehose-iceberg.yml), writes to
an Iceberg table.

Both templates take the same set of parameters:


  * `KinesisStreamName`: the stream where source events are written; defaults to `cloudtrail_events`.
  * `S3Bucket`: the bucket where destination files will be written; no default.
  * `GlueDatabaseName`: name of the Glue database where the table definition is created; defaults to
    `default`.
  * `GlueTableName`: the name of the destionation table; no default.
  * `FirehoseErrorPrefix`: a prefix in the destination bucket where any Firehose errors will be
    written.
  * `FirehoseBufferingInterval`: the number of seconds that Firehose waits to build batches of events;
    default varies depending on whether output is Parquet or Iceberg.
  * `FirehoseFilesizeMB`: the target file size for files produced by Firehose; default varies depending
    on whether output is Parquet or Iceberg.

Notes:

 * The Glue table name is used as the prefix for the table's data files.

 * The Kinesis stream must hold individual CloudTrail events, _not_ notifications S3 bucket notifications.
   See [cloudtrail_to_kinesis](../cloudtrail_to_kinesis) to configure such a stream.

 * The Iceberg template creates a simple transformation Lambda, which lowercases top-level field names
   from the incoming data (for consistency with the Parquet version). If you change this Lambda (for
   example, to snake-case the names), you must also change the `GluePrimaryKey` parameter.

 * The Iceberg template does not configure table optimizations. As-of this writing, the only optimization
   that CloudFormation supports is compaction, and creating that optimization in the same template as the
   table causes CloudFormation to fail. However, this emplate does create (and output) a role that Glue can
   use to perform optimizations.

 * Destroying the CloudFormation stack does _not_ delete data stored in S3; you must do this manually.
