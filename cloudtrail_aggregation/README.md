# CloudTrail Aggregation

This directory contains example programs for the blog post [Aggregating Files In Your Data Lake](https://chariotsolutions.com/blog/post/aggregating-files-in-your-data-lake-part-1/)
and follow-on posts.

It consists of the following pieces:

* [Stage 1](stage-1): a Lambda that aggregates raw CloudTrail log files into compressed NDJSON
  (newline-delimited JSON) files, a day at a time.

* [Stage 2](stage-2): a Lambda that aggregates a month's worth of CloudTrail logs from the files
  produced by stage 1, producing Parquet output. There's also a [Docker version](stage-2-docker)
  in addition to the simple Lambda.

* [Stage 3](stage-3): uses Athena to aggregate a month's worth of CloudTrail logs, again using
  the files produced by stage 1, and again producing Parquet output. This transform is implemented
  using both Airflow and Lambda to invoke an Athena CTAS query to build each partition.
