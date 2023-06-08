This directory contains code used by the blog posts [Athena Performance
Comparison](https://chariotsolutions.com/blog/post/athena-performance-comparison/), and
[Athena/Redshift Performance Comparison](https://chariotsolutions.com/blog/post/performance-comparison-athena-versus-redshift/).
The first looks at different file types when used with Athena queries; the second looks
at the same queries run with Athena, Redshift, and Redshift Spectrum.

If you choose to run this code yourself, beware that you will incur AWS charges. These
include data transfer and storage costs for S3, as well as charges for Glue job execution
and Athena data scans. As always, neither I nor Chariot Solutions are not responsible for
any costs that you incur.


# Generating the data

The examples are based around simulated "clickstream" events for an eCommerce website:
users looking at products, adding items to their shopping cart, and then going through
the checkout process. You use a data generator program  to create these events and write
them to S3 as JSON files, then Glue jobs to produce Avro and Parquet versions.

> **Recommendation:** create a new S3 bucket for this example, so that you can empty and
  delete it when done. It can use default S3 bucket properties (not publicly accessible,
  default encryption, no bucket policy).
  

## Run the data generator to create base (JSON) files

The [data generator](generator/clickstream_generator.py) is a Python program that uses
the `boto3` library to write output files to S3. I recommend using a Python virtual
environment to keep the program self-contained:

```
python3 -m venv .
. bin/activate
pip install boto3
```

Next, run the generator. If you run it without any command-line arguments, it will print help
text an exit; but here's the summary:

```
clickstream_generator.py NUM_EVENTS NUM_USERS NUM_PRODUCTS BUCKET PREFIX FILE_SIZE
```

So, if you want to replicate my test setup of 100,000,000 events, 1,000,000 users, and 10,000
products, with 100000 events per file (replacing my bucket name with yours, of course):

```
generator/clickstream_generator.py 100000000 1000000 10000 com-chariotsolutions-kgregory-example clickstream-json 100000
```

Beware that this particular example took 12 hours to run and generated 19 GB of data.


## Create GZipped JSON variant

If you want to compare plain JSON to GZipped JSON, you'll need to download all of the files,
manually GZip them, then upload again (to a different folder). Given the amount of data, I
recommend doing this from an EC2 instance: you'll almost certainly have more bandwidth, and
you won't pay for data transfer if you're using a publicly-accessible instance. Give this
instance a 100 GB root volume, and pick one of the non-burstable instance types unless you
want to wait a long time.

Assuming that you're running on Linux and have the AWS CLI installed:

1. If you're not using an EC2 instance, change into the `/tmp` directory so that the downloaded
   files will be cleaned up on reboot:

   ```
   cd /tmp
   ```

2. Download the JSON variant:

   ```
   aws s3 sync s3://com-chariotsolutions-kgregory-example/clickstream-json/ clickstream-json/
   ```

3. GZip the files:

   ```
   find clickstream-json -type f | xargs gzip
   ```

4. Upload the GZipped files to a new folder on S3:

   ```
   aws s3 sync clickstream-json/ s3://com-chariotsolutions-kgregory-example/clickstream-json-gz/
   ```

Return to the project directory for the next step.


## Create Avro and Parquet variants

One thing that Glue does very well is bulk transformations. [This Glue script](glue/transform.py)
reads the JSON files from S3 and creates Avro and Parquet variants. You can manually configure the
job, or use [this CloudFormation template](cloudformation/glue_job.yml) (here I use the
[cf-deploy](https://github.com/kdgregory/aws-misc/blob/trunk/utils/cf-deploy.py) tool to
create the stack, but you can use the CloudFormation Console or CLI):

1. Upload the job source code to S3. I use the same bucket as for storing data.

   ```
   aws s3 cp glue/transform.py s3://com-chariotsolutions-kgregory-example
   ```

2. Deploy the CloudFormation template. You need to provide the name of the bucket and the path to
   the script; you won't need to change the data paths unless you uploaded the files to a different
   path. 

   ```
   cf-deploy.py TransformJob cloudformation/glue_job.yml \
                ScriptBucket=com-chariotsolutions-kgregory-example \
                DataBucket=com-chariotsolutions-kgregory-example
   ```

3. Review and run the job from the [AWS Console](https://us-east-1.console.aws.amazon.com/gluestudio/home#/jobs).
   It should run for approximately 10 minutes given the data volume above (and the stack sets a timeout of 30 minutes).


## Create Glue table definitions

At this point all of the table data is in place, but you need to create table definitions. There's
[a CloudFormation template](cloudformation/tables.yml) for this as well. It uses conditional code
to handle the three basic data types (Avro, JSON, and Parquet), and creates a separate Glue database
for each table type.

1. Avro:

   ```
   cf-deploy.py AthenaAvro cloudformation/tables.yml DataType=avro  Bucket=com-chariotsolutions-kgregory-example Prefix=clickstream-avro/
   ```

2. JSON:

   ```
   cf-deploy.py AthenaJSON cloudformation/tables.yml DataType=json  Bucket=com-chariotsolutions-kgregory-example Prefix=clickstream-json/
   ```

3. Parquet:

   ```
   cf-deploy.py AthenaParquet cloudformation/tables.yml DataType=parquet  Bucket=com-chariotsolutions-kgregory-example Prefix=clickstream-parquet/
   ```

If you created GZipped JSON, there's a separate template for that:

```
cf-deploy.py AthenaZippedJSON cloudformation/tables-gz.yml DataType=json  Bucket=com-chariotsolutions-kgregory-example Prefix=clickstream-json-gz/
```


# Running the Queries

I've provided the Avro version of most of these queries. Replace `athena-avro` with `athena-json`, `athena-json-gz`,
or `athena-parquet` to run the other variants. The one exception is query 2, which uses different date logic for
each data type.

## Query 1: top products added to cart

```
select  productid, sum(quantity) as units_added
from    "athena-avro"."add_to_cart"
group   by productid
order   by units_added desc
limit   10;
```


## Query 2: top products added to cart in specific date range

To run this query, you need to first identify the range of generated data. I'm using the Parquet tables here because
they have the nicest date support:

```
select  date_trunc('hour', "timestamp"), count(*)
from    "athena-parquet"."add_to_cart"
group   by 1
order   by 1 desc;
```

Pick a range of dates that gives you whatever desired percentage of the table you want to query. Then replace the dates
in these queries:

### Avro

```
select  productid, sum(quantity) as units_added
from    "athena-avro"."add_to_cart"
where   from_unixtime("timestamp"/1000000) between from_iso8601_timestamp('2023-04-25T21:00:00') 
                                               and from_iso8601_timestamp('2023-04-25T22:00:00')
group   by productid
order   by units_added desc
limit   10;
```

### JSON / GZipped JSON

Change the database name to `athena-json-gz` for GZipped JSON.

```
select  productid, sum(quantity) as units_added
from    "athena-json"."add_to_cart"
where   "timestamp" between '2023-04-25 21:00:00' 
                        and '2023-04-25 22:00:00'
group   by productid
order   by units_added desc
limit   10;
```

### Parquet

```
select  productid, sum(quantity) as units_added
from    "athena-parquet"."add_to_cart"
where   "timestamp" between from_iso8601_timestamp('2023-04-25T21:00:00') 
                        and from_iso8601_timestamp('2023-04-25T22:00:00')
group   by productid
order   by units_added desc
limit   10;
```


## Query 3: products ranked by difference between views and adds

It would be nice to add in a select-list expression `views - adds`, but apparently Athena
can not handle referencing an aliased expression in the same select list: it fails with
the message "Column 'views' cannot be resolved".

One of the key points of this query is that it involves almost all of the columns of the
two tables, so limits the ability of Parquet to limit scanned data.

```
select  pp.productid, 
        count(distinct pp.eventid) as views, 
        count(distinct atc.eventid) as adds
from    "athena-avro"."product_page" pp
join    "athena-avro"."add_to_cart" atc 
on      atc.userid = pp.userid 
and     atc.productid = pp.productid
group   by pp.productid
order   by views - adds desc
limit   10
```


## Query 4: abandoned carts

I included this query because data warehouses often have issues with outer joins. But
looking at the query's execution plan, it's almost identical query 3. It does, however,
involve fewer columns, so should give Parquet an edge in terms of data scanned.

```
select  pp.productid, 
        count(distinct pp.eventid) as views, 
        count(distinct atc.eventid) as adds
from    "athena-avro"."product_page" pp
join    "athena-avro"."add_to_cart" atc 
on      atc.userid = pp.userid 
and     atc.productid = pp.productid
group   by pp.productid
order   by views - adds desc
limit   10
```


# Cleaning Up

To delete the Glue job and Athena table definitions, delete the CloudFormation stacks.

Assuming that you created a dedicated bucket for this project, you can remove it with
the CLI:

```
aws s3 rb --force s3://com-chariotsolutions-kdgregory-example
```
