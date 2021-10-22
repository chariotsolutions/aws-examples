This directory contains example Athena table definitions and queries for CloudTrail logs.
It exists to support [this blog post](https://chariotsolutions.com/blog/post/rightsizing-data-for-athena/).

The table definitions are based on the definition provided [here](https://docs.aws.amazon.com/athena/latest/ug/cloudtrail-logs.html),
with the addition of partitioning information. There are four definitions:

* `raw_unpartitioned.ddl`

  The base table definition for uploaded CloudTrail log files, without any partitions.
  Queries against this definition will scan the entire dataset.

* `raw_partitioned.ddl`

  The based CloudTrail table definition using partition projection for account ID,
  region, and date. 
  
* `consolidated.ddl`

  A table definition that is applied to a "consolidated" dataset, in which all of the
  event records are combined into files based on date. The table definition partitions
  by date, following the uploaded files.

* `single_file.ddl`

  A table definition that's applied to a dataset consisting of a single file with all
  of the event records. There isn't any partitioning.

To use these table definitions you will need to edit the S3 location to correspond to
your CloudTrail data store. For the `raw_partitioned` definition you'll also have to
provide a list of the account IDs used for partitioning.

Each of the table definitions has a corresponding SQL query that counts the number of
records by account, region, and date. These queries use partitioning columns where
available, otherwise they extract the information from the parsed data.
