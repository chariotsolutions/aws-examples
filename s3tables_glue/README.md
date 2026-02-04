# Example of using S3 Tables with Spark SQL under Glue 5.0

This script create a summary of event counts from an S3 Table containing CloudTrail events.
It is intended to give you a starting place for your own S3 Tables Glue jobs.

## Prerequisites

* The table containing CloudTrail data. See [this project](../cloudtrail_firehose) for a
  CloudFormation template that creates this table and an AWS Data Firehose to populate it.
  Alternatively, [this document](populate_cloudtrail.md) explains how to create the table
  from raw CloudTail files on S3.

* A standard S3 bucket that will be used to hold the Glue script for deployment. You may
  already have such a bucket: if you manually create a Glue job, Glue creates a bucket
  with the name `aws-glue-assets-ACCOUNT-REGION` (where `ACCOUNT` is your account number
  and `REGION` is your current region).

## Deployment process

1. Upload the file `glue_job.py` to your S3 staging bucket.

2. Create a CloudFormation stack from the template `cloudformation.yml`. You'll need to
   provide several parameters, which are documented in the stack.

3. Grant LakeFormation permissions to the execution role created by the stack (this
   can't currently be done in CloudFormation, because the relevant resource doesn't
   support S3 Tables catalogs). The role name starts with the stack name.

   If you just want to read from this table, grant `Describe` permissions on the S3
   Table Bucket catalog and database, and `Select` permission on the source table.
   If you want to generally experiment with Glue, grant Super permissions on catalog,
   database, and all tables.

## Running the job

Running the job is easy: go to the [ETL Jobs](https://console.aws.amazon.com/gluestudio/home?/jobs)
page in the Console, open the job, and press the big orange "Run" button. It takes about 1 minute
30 seconds to produce the output table (a lot of this is the overhead of starting Glue jobs, a
reason to put more than a single query in your scripts).

If you run the script a second time it takes the same minute and a half, but does nothing because
the creation query uses `CREATE TABLE IF NOT EXISTS`. If you're feeling daring, you can add a
`DROP TABLE` command before creating the output table.

And when you're done with the table, you'll need to manually delete it. This has two parts: first,
go into the Glue Data Catalog and delete the output table there. Then go to S3 and delete the folder
that holds the table data.


## Notes

The Glue execution role created by this template has read and write permissions on both the S3
Table Bucket and the "traditional" S3 bucket. This was done intentionally, to allow this script
to be the base for exploration. If you want to limit to just read from the Table Bucket and
write to the single location in the traditional bucket, do the following:

* Update the resource in policy `S3` to the following:

  ```
  !Sub "arn:aws:s3:::${TargetBucket}/${TargetPrefix}${TargetTable}/*"
  ```

* Update the policy `S3Tables` to just allow the following actions: `s3tables:GetTableBucket',
  `s3tables:GetNamespace', `s3tables:GetTable', and `s3tables:GetTableData".

* Update the LakeFormation grants to only allow Describe and Select on the specific table.

If you don't grant Lake Formation permissions to `Describe` the S3 Table Bucket catalog and
database, and to `Select` from the source table (or all tables), you'll get the following
error (with your table's name in place of mine):

> AnalysisException: [TABLE_OR_VIEW_NOT_FOUND] The table or view `example`.`default`.`cloudtrail`
  cannot be found

The `TARGET_S3_URL` parameter uses an `s3a://` URL for the target data location, rather than
the more common `s3://` URL. When using the latter, Glue will create an empty folder, named
after the target table but with `_$folder$` appended. Not only does this get in the way of
least-privilege permissions, is also clutters the S3 bucket. 
