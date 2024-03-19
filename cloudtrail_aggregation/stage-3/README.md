# Athena Data Transformation

This folder contains an example of using Athena to aggregate and transform CloudTrail data.
To develop this I used the aggregated data produced by my [stage-1](../stage-1) aggregation,
but it's easy to adapt to raw CloudTrail data.

The most interesting part of this example is that I use a `CREATE TABLE AS` (CTAS) query to
generate the monthly aggregations, which are stored as partitions of a long-lived table.


## The Long-lived Table

The long-lived table is how you query the CloudTrail events. It is partitioned by month
and year, and uses partition projection rather than storing a list of partitions in the
Glue data catalog.

The file [table.ddl](table.ddl) contains the DDL to create this table. You must edit
this file before use, raplacing `MY_BUCKET` with your actual S3 bucket (you may also
change the table name, which is also used as the bucket prefix from `cloudtrail_athena`
to something else). After editing, use the Athena Console to create the table.

You'll note that this table definition does not contain struct fields or arrays, unlike
the AWS-provided DDL for accessing raw CloudTrail data. Instead, these fields are turned
into stringified JSON, and must be parsed for use.


## Creating a Partition

Each monthly partition in the long-lived table is created using a separate Athena query.
The specific steps are:

1. If you're running the transform multiple times, you need to delete any data already
   in the partition location on S3, as well as the temporary table in the data catalog
   (if it exists).
2. Edit the [CTAS query](ctas.ddl) to specify the source table, destination location, and
   date range.
3. Run the CTAS query.
4. Delete the table produced by the CTAS query. This does not delete the table's data,
   which can be accessed via the long-lived table.

You can perform these steps manually using the Concole. I've also provided a Lambda and
Airflow DAG that perform them programmatically.


## Permissions Required

Whether you run in Airflow, Lambda, or the Console, you need a permission policy that lets
you read and write S3, run Athena queries, and update the Glue data catalog.

For a Lambda deployment, the provided CloudFormation template generates this policy. For an
Airflow deployment, or to manually execute the queries, the file [policy.json](policy.json)
contains a sample policy. To use, edit and replace the following dummy values whereever they
appear:

* `AWS_ACCOUNT_NUMBER`, `AWS_REGION`

  The account and region where the Athena database lives. These are used to contruct non-S3
  ARNs.

* `ATHENA_WORKGROUP`

  The name of the [Athena workgroup](https://docs.aws.amazon.com/athena/latest/ug/workgroups.html)
  used to run these queries. If you have not configured workgroups, use "primary" (a predefined
  workgroup available in all accounts/regions).

* `ATHENA_WORKGROUP_BUCKET`, `ATHENA_WORKGROUP_PREFIX`

  The bucket and prefix where Athena stores query results for the specified workgroup.

* `SOURCE_BUCKET`, `SOURCE_PREFIX`

  The bucket and prefix for the source table. This is used to grant read permissions to Athena.

* `DST_BUCKET`, `DST_PREFIX`

  The bucket and prefix for the destination table. This is used to grant write/delete permissions
  to Athena.

* `GLUE_DATABASE`

  The name of the Glue database where the source table lives and the partition table will be
  written. If you have not configured databases, use "default".

Note that the policy separates source and destination buckets, even though most deployments
will use a single bucket; feel free to combine those statements. Also note that there's a
separate statement that controls access to the default results bucket for Athena, which
might also be the same as that used for table data.

You may also wish to relax the resources covered by each policy statement, especially if
you use Athena for multiple queries.


## Running as a Lambda

As with the previous examples this Lambda is invoked via SQS, using either an explicit
month/year or an EventBridge message. To deploy, there's a [CloudFormation template](cloudformation.yml),
and like the previous examples you must update the Lambda code from the file [lambda.py](lambda.py).

There are a more parameters for this CloudFormation template than that of earlier stages.
In particular, the source and destination table names must be provided in addition to the
bucket/prefix combinations. We also require the Athena workgroup configuration (bucket,
prefix, and workgroup name), and the Glue database name.


## Running in Airflow

I will preface this section by noting that I am a novice Airflow user. If you have suggestions
for a better implementation, feel free to open an issue in this repository.

My [Airflow DAG](airflow_dag.py) performs the steps listed above: it deletes any existing
temporary table or S3 objects, executes the CTAS, and then deletes the temporary table.
To do this, it uses components from the Amazon AWS provider:
[S3DeleteObjectsOperator](https://airflow.apache.org/docs/apache-airflow-providers-amazon/stable/operators/s3/s3.html#delete-amazon-s3-objects),
[AthenaOperator](https://airflow.apache.org/docs/apache-airflow-providers-amazon/stable/operators/athena/athena_boto.html#run-a-query-in-amazon-athena),
[AthenaSensor](https://airflow.apache.org/docs/apache-airflow-providers-amazon/stable/operators/athena/athena_boto.html#wait-on-amazon-athena-query-results),
and the [Amazon Web Services Connection](https://airflow.apache.org/docs/apache-airflow-providers-amazon/stable/connections/aws.html).

To use this DAG, you'll need to at least edit the `BUCKET_NAME` constant, replacing "MY_BUCKET"
with your actual bucket name.

You may also want to change the connection referenced by the `AWS_CONNECTION_ID` constant. If
you're using AWS Managed Airflow (MWAA), then the existing ("aws_default") connection refers
to the Airflow execution role; add the above policy to that role if it doesn't already grant
similar permissions. When I was developing the DAG I used an IAM user that only had that
policy attached; there may be better approaches, but as I said, I'm an Airflow novice.
