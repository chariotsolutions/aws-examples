# CloudTrail Aggregation

This directory contains example programs for the blog post [Aggregating Files In Your Data Lake](https://chariotsolutions.com/blog/post/aggregating-files-in-your-data-lake-part-1/).
It consists of the following pieces:

* [Stage 1](stage-1): a Lambda that aggregates raw CloudTrail log files into compressed NDJSON
  (newline-delimited JSON) files, a day at a time.

* [Stage 2](stage-2): a Lambda that aggregates a month's worth of CloudTrail logs from the files
  produced by stage 1, producing Parquet output. There's also a [Docker version](stage-2-docker)
  in addition to the simple Lambda.
