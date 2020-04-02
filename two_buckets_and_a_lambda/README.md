# Two Buckets and a Lambda: a pattern for S3 file transformation

This is the example code for [this blog post](#). It implements a simple web-app in
addition to the actual processor Lambda.

![Architecture Diagram](static/images/webapp-architecture.png)


## Deploy

There's a single [CloudFormation](scripts/cloudformation.yml) script that creates all
of the components. However, the sample web-app requires some static HTML and JavaScript,
so there's a deployment script (you must have the AWS CLI installed to run this):

```
scripts/deploy.sh STACK_NAME BASE_BUCKET_NAME
```

* `STACK_NAME` is the name for your stack; it must be unique within the account/region.

* `BASE_BUCKET_NAME` is used to name the three buckets; the suffixes `-uploads`, `-archive`,
  and `-static` will be applied to it. Bucket names must be globally unique; I recommend a
  reverse domain name that includes the stack name: `com-example-mystack` (note that bucket
  names must be lowercase).

This script should take less than five minutes to run. However, it uses the CLI's "wait"
command, which doesn't time out until an hour has elapsed. You can either get the status
of the stack via the CLI in another window, or watch the creation events in the console.

When it's done, it will write the HTTPS endpoint of the example. You can then open that
link in your browser.


## Use

If you go to the link, you'll see the rather uninspiring UI shown below. I recommend also
opening your browser's Developer Tools, so that you can see the console and network traffic.

![Two Buckets UI](static/images/webapp-ui.png)

Click "Browse" to select a file, then either "Upload via signed URL" or "Upload via
restricted credentials" to upload that file to the staging bucket.

If you look at the staging bucket in the AWS console, you probably won't find your file
there: it will be in the archive bucket, and there will be a message in CloudWatch logs.

Feel free to extract the temporary credentials from the API response and try to use them
to upload another file.


## Undeploy

The counterpart of the deploy script is the undeploy script. This will force-delete all 
of the buckets and then delete the CloudFormation stack.

```
scripts/deploy.sh STACK_NAME BASE_BUCKET_NAME
```


## Implementation Notes

In addition to demonstrating the "two buckets" processing Lambda, this example also provides
examples of uploading the files to S3. It is implemented as a simple web-app, using API
Gateway to serve both static content and two Lambda-backed endpoints (`/api/credentials`
and `/api/signedurl`). To simplify the example, I use "proxy" integations for all three.

The client-side JavaScript code is intended as a tutorial, so breaks out the various steps
as separate functions and does not rely on chained promises. It also creates the two
operational functions in global scope, and explicitly attaches them to the buttons in HTML.
Scroll to the end of the file to see this function.

There is one bit of the JavaScript that requires some extra explanation

```
const rootUrl = window.location.href.replace(/[^/]*$/, "");
const queryUrl = rootUrl + "api/signedurl";
```

One of the quirks of API Gateway is that it deploys "stages": you can have a development
stage and a production stage of the same API (or, more realistically, a `v1` and `v2`
stage). When you do this, the stage name is part of the URL:
`https://fq14qko999.execute-api.us-east-1.amazonaws.com/dev/api/credentials`. In a
typical web-app, you would refer to an endpoint within JavaScript or HTML without
the hostname: `/api/credentials`. However, this will fail when running with API Gateway,
_except in the case where you're using a custom domain name to access the endpoint._

When the JavaScript file is loaded, `window.location.href` contains the URL of the web
page: `https://fq14qko999.execute-api.us-east-1.amazonaws.com/dev/index.html` in this
case. So the regex strips off the `index.html` part, and `queryUrl` adds the hardcoded
path to the relevant Lambda endpoint.
