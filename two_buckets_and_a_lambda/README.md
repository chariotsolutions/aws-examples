# Two Buckets and a Lambda: a pattern for S3 file transformation

This is the example code for [this blog post](#).

This is actually a rather complex example, consisting of _three_ buckets, _three_ Lambdas,
and an API Gateway:

* Bucket #1: static code
  Holds web pages and JavaScript for the demo app.

* Bucket #2: staging 
  This is the bucket where files will be uploaded to.

* Bucket #3: archive 
  This is the bucket where files are moved to after processing.

* Lambda #1: file handler 
  This is the core Lambda; it is triggered by every new file, reports that file's size,
  and moves it into the destination bucket.

* Lambda #2: signed URL generator
  An API endpoint that will genera signed URLs that allow an explicit PUT to S3.

* Lambda #3: limited credentials generator
  An API endpoint that will generate credentials with permission to perform a
  multi-part upload of a single object to S3.


## Usage

First, run the deployment script (you must have the CLI installed):

```
./deploy.sh STACK_NAME BASE_BUCKET_NAME
```

`STACK_NAME` is the name for your stack; it must be unique within the account/region.

`BASE_BUCKET_NAME` is used to name the three buckets; the suffixes `-uploads`, `-archive`,
and `-static` will be applied to it. Bucket names must be globally unique; I recommend a
reverse domain name that includes the stack name: `com-example-mystack` (note that bucket
names must be lowercase).

This script should take less than five minutes to run. However, it uses the CLI's "wait"
command, which doesn't time out until an hour has elapsed. You can either get the status
of the stack via the CLI in another window, or watch the creation events in the console.



## Implementaion Notes
