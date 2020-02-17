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

### Deployment

Deployment is a two-step process: the first is to create all of the infrastructure as
a CloudFormation stack, the second is to upload static content.

```
aws s3 cp static/index.html s3://com-chariotsolutions-twobuckets-static/index.html               --acl public-read --content-type text/html
aws s3 cp static/js/signed-url.js s3://com-chariotsolutions-twobuckets-static/js/signed-url.js   --acl public-read --content-type text/javascript
aws s3 cp static/js/credentials.js s3://com-chariotsolutions-twobuckets-static/js/credentials.js --acl public-read --content-type text/javascript
```


### Running


### Undeployment

To undeploy this example, you must first empty the S3 buckets (because CloudFormation
won't delete a bucket that's not empty):

```
```

Then, delete the CloudFormation stack, which will take down everything it created.


## Implementaion Notes
