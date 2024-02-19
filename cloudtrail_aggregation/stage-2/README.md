# Stage 2: Monthly Aggregation

This stage takes a month of NDJSON files produced by [stage-1](../stage-1) and 
creates a single Parquet file, written to a different destination.

This presents a challenge, as Parquet requires a schema that describes all fields in
the event, while CloudTrail events have nested objects with dramatically different
contents for different event types. To support these differences, common top-level
fields are converted directly to Parquet, while all nested objects are stringified
and stored as Parquet strings.

The Parquet conversion is handled by the [PyArrow](https://arrow.apache.org/docs/python/index.html)
library. This library has the drawback that it includes a native component, and you
must use the version appropriate for a particular Python implementation, operating
system, and processor architecture. It's also big: PyArrow plus its required NumPy
dependency are together larger than the maximum deployment size for a Lambda ZIP
bundled.

I solve this problem in two ways: with Lambda layers and a Lambda Container Image.
Of these, I think the container image is a better choice.


## Prerequisites

You must have an existing bucket that contains source NDJSON files, as well as a
destination bucket for the Parquet files (they may be the same bucket, using
different prefixes). If this bucket is in a different account from that running the
Lambda, it must have a bucket policy that allows `s3:ListBucket`, `s3:GetObject`,
and s3:PutObject` for the invoking account.


## Layers

A deployed Lambda can have up to five layers, each of which can be up to 50 MB of
compressed content. Layers can be a great way to package dependencies that are used
by multiple Lambdas, keeping those dependencies out of the individual deployment
bundles.

For Python Lambdas, dependencies must be installed in the `python` directory; one
way to do that (which works well with build scripts) is to use pip's `-t` option:

```
pip install -r requirements.txt -t python
zip -r /tmp/layer.zip python
```

Unfortunately, when using `pyarrow` or other library that includes a binary component
(such as `psycopg-binary`), you can't just run those commands on an arbitrary build
machine and expect the resulting layer to work. The reason is that the binary module
is tied to a specific Python version and processor architecture.

As long as the architecture matches (ie, your build machine is x86 and you're deploying
an x86 Lambda), you can use one of the AWS-provided Lambda base images, as I describe
[here](https://chariotsolutions.com/blog/post/building-and-deploying-lambdas-from-a-docker-container/)).

First, start up the appropriately-versioned image:

```
docker run -it --rm \
       --entrypoint /bin/bash -v /tmp:/build \
       amazon/aws-lambda-python:3.12
```

Note that these images start Python by default; I tell it to run a shell with the
`--entrypoint' option. I also bind-mount `/tmp` on my workstation as `/build` in the
container. Then, from inside the container, I can run the following commands to
create version-appropriate ZIP files:

```
cd /tmp
pip install -t python pyarrow
zip -r /build/pyarrow.zip python/pyarrow*
zip -r /build/numpy.zip python/numpy*
```

Now you can upload these ZIP files as Lambda layers. Note that they were created
with the default user (root) of the Docker container, so you'll need to use `sudo`
to clean them up (or just reboot your system).

To be honest, that's a _lot_ of work, and isn't easily integrated into a build
pipeline. I think it's better to use a Lambda Container Image.


## Lambda Container Image

To build the container image, you must have Docker installed. Then, from this directory, run:

```
docker build -t cloudtrail-aggregation-stage2 .
```

The next step is to create an [ECR repository](https://docs.aws.amazon.com/AmazonECR/latest/userguide/what-is-ecr.html)
and upload the image there (or use your preferred container registry).


## CloudFormation

There are two CloudFormation templates in this directory:

* [cloudformation.yml](cloudformation.yml) for a "simple" deployment with Python code
  and layers. To use this template, you must have previously created those layers as
  described above. You must also manually replace the Lambda's code with the contents
  of [lambda.py](lambda.py).
* [cloudformation-lci.yml](cloudformation-lci.yml) for a deployment with Lambda Container
  Images. To use this template, you must have previously built the Docker image and 
  uploaded it to a container registry.

Both templates require configuration for the source and destination bucket/prefix. The
"simple" deployment additionally needs the ARN of the required layers, while the LCI
deployment requires the ARN of the image. There are other parameters that are documented
in the templates, but which can normally be left as defaults.


## Triggering the Lambda

Unlike the "stage 1" Lambda, this example does not include an EventBridge Scheduler rule.
The reason is that you might want to aggregate at the start of each month, or every day
once the daily Lambda has run. In the latter case, while you could implement a scheduler
rule, I think it would be better if the stage-1 Lambda published an event when it was
done.


## Creating an Athena table

The file [table.ddl](table.ddl) contains DDL for the monthly aggregation table. Edit
this file, replacing `BUCKET` and `BASE_PREFIX` with the actual values for your data
(eg, `cloudtrail-monthly`), then paste into an Athena query window.
