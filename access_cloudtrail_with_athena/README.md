This directory contains example Athena table definitions and queries for CloudTrail logs.
It exists to support [this blog post](https://chariotsolutions.com/blog/post/rightsizing-data-for-athena/),
as well as other examples.

The table definitions are based on the definition provided [here](https://docs.aws.amazon.com/athena/latest/ug/cloudtrail-logs.html),
with changes to support different partitioning schemes:

* `raw_unpartitioned.ddl`

  A base table definition for uploaded CloudTrail log files, without any partitions.
  Queries against this table will scan the entire dataset.

* `raw_partition_projection.ddl`

  The base table definition, updated to use partition projection for account ID, region,
  and date.

  Note: this must be updated with your accounts and the regions that you wish to query.

* `raw_partition_injection.ddl`

  The base table definition, updated to use partition injection for account ID, region,
  and date. Unlike the projection variant, you must specify predicates on all of these
  columns.
  
* `consolidated.ddl`

  A table definition that is applied to a "consolidated" dataset, in which all of the
  event records are combined into NDJSON files based on date. The table definition
  partitions by date, following the uploaded files.

* `single_file.ddl`

  A table definition that's applied to a dataset consisting of a single file with all
  of the event records. There isn't any partitioning.

For each of these table definitions, there's an accompanying SQL query that counts
the top-10 events for a given date range, account ID, and region.

Notes:

* Replace `BUCKET` with the name of your actual bucket.

* All table definitions assume that files will reside at the top of the target bucket.
  If you store your files under a prefix, you must add it to `LOCATION` and
  `storage.location.template` configuration.

* For partitioned tables, `storage.location.template` is configured for an organization,
  with `ORG_ID`. Replace this with your actual organization ID, or remove it (and the
  following slash) if your CloudTrail repository represents a single account.

* Date partitions are configured to start with November 13, 2013, the [date that CloudTrail
  was announced](https://aws.amazon.com/about-aws/whats-new/2013/11/13/announcing-aws-cloudtrail/).
  Update to match your actual data to avoid inefficient queries.
