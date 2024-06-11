An example of connecting a data source exposed via WebSocket to a Kinesis stream.

There are two parts to this example, both of which run as services in ECS:

* Server that listens for web-socket connections, and sends a series of messages
  to the client.
* Client that connects to the server, and forwards all received messages to a
  Kinesis stream.

The client will reconnect (after a short pause) if the connection is broken
(this happens intentionally when the server closes the connection, but also
if the server is restarted). It runs as a service so that it is restarted
automatically on any fatal errors.

In the real world, the server would need to provide some way to start sending
messages from a known point, and the client would need to preserve that point
to restart cleanly. The client or downstream processing must also be prepared
for duplicate records.


## Building

Both the client and server are packaged as Docker images, based on the Python
base image. To build:

```
docker build -t ws2k_server -f Dockerfile.server .
docker build -t ws2k_client -f Dockerfile.client .
```


## Deploy via CloudFormation

This project includes a [CloudFormation template](cloudformation.yml) that deploys the
various components of the example. To avoid the chicken-and-egg problem of an ECS service
that relies on an ECR repository created by the same template, deployment is a multi-step
process.

**Warning:** this template creates multiple resources that incur costs from AWS. These
costs are generally low for an experimental deployment, but _don't forget to delete the
stack when you're done!_


### Step 1: Initial deployment

This step creates the basic infrastructure, including the Kinesis stream, ECS task
definitions, Cloud Map namespace, and related resources.

To deploy, you will need to provide the following parameters:

* `VpcId`, `SubnetIds`

  Identifies the VPC and subnets where the client and server will be deployed. You
  must specify at least one subnet, but can specify more. If you specify more, 
  then the services will be deployed arbitrarily (and you may pay for cross-AZ
  data transfer as a result).

  If you don't have a NAT, then you must use public subnets. If you do have a NAT
  (or Interface Endpoint for Kinesis), you can use private subnets unless you want
  to connect to the server from outside of the VPC.

* `AssignPublicIPs`

  If you deploy into public subnets, this must be set to "true"; if into private
  subnets, it should be set to "false". The default is "false", given that public
  IPs incur a per-hour cost.


### Step 2: Upload Docker images

To complete this step, you must have built the client and server images as described
above. Then, perform the following steps, replacing `0123456789012` by your account
ID, and `us-east-1` by your region. 

1. Provide login credentials to your local Docker daemon:

   ```
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com
   ```

2. Tag the images with a repository-specific tag:

   ```
   docker tag ws2k_client:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/ws2k_client:latest
   docker tag ws2k_server:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/ws2k_server:latest
   ```

3. Push the images to the repository

   ```
   docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/ws2k_client:latest
   docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/ws2k_server:latest
   ```

As an alternative, go to each repositority in the AWS Console, click on the
"View push commands" buttons, and copy/paste each of the commands _except_
the ones to build the images.


### Step 3: Enable Server

The server must be running in order to update its DNS entry. While the stack
should work if you enable both at the same time, you will probably see error
messages from the client.

To enable the server, update the CloudFormation stack, and set the `EnableServer`
parameter to "true".

You can configure the rate at which the server attempts to send messages using
the following two parameters:

* `ServerSendCount`

  The number of messages that the server will send for each connection. The
  default is 60.

* `ServerSendSleep`

  The fractional number of seconds that the server will sleep between each
  message. The default is 1.0; increase to see where the client can't keep up.

If you want to terminate the server without tearing down the stack, you can
update the stack with this parameter set to "false".


### Step 4: Enable Client

Much like the server, you enable the client by updating the CloudFormation stack.
In this case set the `EnableClient` parameter to "true". And to terminate the client,
update the stack and set it to "false".


### Other Parameters

The CloudFormation template has several other parameters, all of which have sensible
defaults. If you want to change them, here they are:

* `CloudMapNamespaceName`

  The namespace used for Cloud Map service lookups. Cloud Map creates a Route 53
  local zone with this name. The default of "ws2k" should not conflict with any
  zone that you might already have.

* `ClientImageName`, `ClientImageTag`

  The image name (default "ws2k_client") and tag (default: "latest") for the client
  image. The image name will be the name of the ECR repository holding the client
  image.

* `ServerImageName`, `ServerImageTag`

  The image name (default "ws2k_server") and tag (default: "latest") for the server
  image. The image name will be the name of the ECR repository holding the server
  image.

* `ServerHostName`, `ServerPort`

  The host name (default: "server") and port (default: 8000) for the server. The host
  name will be exposed via Cloud Map, so available via DNS from the client.


## Running Locally

If you don't want to spin up a lot of infrastructure in AWS, you can run the example
on your local machine, either using Docker or directly in Python. You will, however
have to create a Kinesis Stream to receive the messages.


### Python

To run in Python, you first need to install the `boto3` and `websockets` libraries.
I don't provide a requirements file, so you'll have to do this manually. I recommend
creating a virtual environment.

```
python -m venv .venv
. .venv/bin/activate
pip install boto3 websockets
```

In one window, run the server. You can specify the port number via environment
variable, as I do here, or use the default of 8000. You can also control the
rate at which the server sends (using sleep time) and number of messages.

```
LISTEN_PORT=9999 SEND_SLEEP=0.25 SEND_COUNT=100 python server.py
```

In another window, start the client. This window must have AWS credentials that allow
writing to Kinesis. The stream must already exist; if you're not using the CloudFormation
template, you'll need to create it via the Console or CLI.

```
SERVER_URL="ws://localhost:9999" STREAM_NAME=example python client.py
```


### Docker

You can run the Docker images locally, with the caveat that you must reference the server
by the local machine's IP address, not `localhost` (or define a custom network with DNS
resolution).

To run the server (note that I use default configuration):

```
docker run -it --rm --name ws2k_server \
       -p 8000:8000 \
       ws2k_server:latest
```

And the client (replacing 192.168.4.106 by whatever address is correct for you):

```
docker run -it --rm --name ws2k_client \
       -e SERVER_URL="ws://192.168.4.106:8000" \
       -e STREAM_NAME="example" \
       -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -e AWS_SESSION_TOKEN -e AWS_DEFAULT_REGION \
       ws2k_client:latest
```

Note that I pass in AWS credentials as environment variables. You could also bind-mount
your `$HOME/.aws` directory, but I find the variables easier. You can omit `AWS_SESSION_TOKEN`
if not running with an assumed role.


### Local Client, Remote Server

If you want to experiment with changes to the client, you won't want to constantly redeploy.
Instead, run the client locally, pointing to the IP address of the server running in AWS. To
do this, you must do the following:

* Allow traffic from your local machine through the security group attached to the server.
  Easiest way to do this is add an all-traffic ingress rule via the Console.

* Deploy the server into a public subnet, with a public IP address.

* Get that IP address. To do so, use the Console to find the task running as part of that
  service (this involves opening the cluster, then clicking on the server inthe cluster's
  service list, then clicking on the task ID in the service's task list). Go to the
  "Networking" tab and you'll be able to copy the public IP address.
