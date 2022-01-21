This example deploys a Squid proxy to serve as a controlled path between AWS
applications and external services (including AWS). This can help to mitigate
remote-code execution vulnerabilities, by blocking connections to the attacker's
endpoint.

Squid is perhaps known as a cache server, which sits between users and the sites
they use, storing artifact (such as images) so that they don't need to be pulled
from the origin server whenever viewed. In this example, however, we use it as a
simple "forward" proxy, which sits between an application and the web sites that
it uses, and decides whether to allow the connection.


We chose the Squid proxy because it is simple to configure for our needs (although
the [complete set of config directives]() is
quite large).

Other options include Apache httpd and HAProxy; there's also a
third-party module for nginx. If you are more comfortable with a different server,
feel free to adapt this example to use it.


## Configuring the proxy

To configure a proxy, you start with [acl]()
directives that identify sources and destinations. For example:

```
acl allowed_dests dstdomain .amazonaws.com
```

This definition says that the `allowed_dests` ACL includes any requests where the
destination hostname ends with `.amazonaws.com`. You can use multiple ACL definitions
with the same name: the example config also includes `docs.aws.amazon.com` in the
`dstdomain` ACL, and you can add as many more hosts/domain as you'd like.

The example also defines two ACLs that are based on IP addresses: `localnet` and
`to_localnet`. These specify all possible "private" network addresses; you can
delete any that don't apply to your VPC.

These ACLs are then combined using the following rules:

```
http_access allow localnet to_localnet
http_access allow localnet allowed_dests
http_access deny all
```

The first rule allows inbound traffic from the local network to connect to destinations
that are also in the local network. The second allows inbound traffic to connect to the
allow-listed hosts. And the third denies everything else.

The configuration file contains a few more directives, taken from the configuration file
for the base image.


## Building and deploying

This example has the following prerequisites:

* Docker command-line tools to build and push the image.
* An [ECR Repository](https://docs.aws.amazon.com/AmazonECR/latest/userguide/Repositories.html)
  to hold the image and make it available to ECS.
* A [Cloud Map](https://docs.aws.amazon.com/cloud-map/latest/dg/what-is-cloud-map.html)
  namespace with Route53 hosted zone. In the examples, I use a namespace with the name
  "internal". _Do not_ use the Console's suggested namespace of "private", as that is
  a reserved domain in DNS and you won't be able to resolve hostnames in it.

After you've customized the Squid configuration to your liking, change into the `docker`
directory, then build and publish the image. This involves the following steps; I show
the commands for my repository, you can get the commands for yours from the Console
("View push commands"):

1. Provide Docker with the credentials to push to the respository

   ```
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com
   ```

2. Build the image.

   ```
   docker build -t squid_proxy .
   ```

3. Tag the image with the repository URI.

   ```
   docker tag squid_proxy:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/squid_proxy:latest
   ```

4. Push the image to the repository

   ```
   docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/squid_proxy:latest 
   ```

Now you're ready to deploy the proxy as an ECS service. I've provided a [CloudFormation
template](cloudformation.yml) to do this. You'll need to provide it with the following
parameter values (several of which have defaults:

* The name of the proxy service. This defaults to "squid_proxy", but you may want to use
  a different name.
* The name of the ECS cluster where the proxy will be deployed. This defaults to "default".
* The Cloud Map namespace ID, which you can get from the Console.
* The fully-qualified name and tag of the published Docker image (the last argument to
  the `push` command; eg, `123456789012.dkr.ecr.us-east-1.amazonaws.com/squid_proxy:latest`).
* The ID and IP address CIDR of the VPC where the image will be published. The CIDR can
  be copied from the Console, and is used to create a security group for the service.
* The IDs of one or more _public_ subnets in the VPC. The proxy must be deployed into a
  public subnet so that it can communicate with AWS and other publicly-accessible sites.

It will take approximately five minutes to deploy the service, which consists of two 
Fargate containers. Once both containers are up and running, you can use the proxies.


## Examples

For each SDK, we've provided two example programs that retrieve the user's current
identity (equivalent to running `aws sts get-caller-identity` from the command line).
One example uses explicit proxy configuration, while the other does not (but can be
configured at runtime).

To run the examples, you will need valid AWS credentials. These can be configured in
any of the standard ways (environment variables, `aws configure`, instance metadata).

All examples use the hostname `squid_proxy.internal` to refer to the proxy. If you
changed the name when deploying, or your Cloud Map namespace uses a different DNS
name, update before running.


### Python

Both examples are written as executable programs using a Linux "shebang" for Python.

To make [no_proxy.py](examples/python/no_proxy.py) use the proxy server, you can set
the `HTTPS_PROXY` environment variable:

```
export HTTPS_PROXY=http://squid_proxy.internal:3128
./no_proxy.py
```


### Java version 1 SDK

To build:

```
mvn clean package
```

To run the explicit proxy version (will fail if you don't have a proxy server running,
with the DNS name `squid_proxy.internal`):

```
java -cp target/proxy-example-v1-1.0.0.jar com.chariotsolutions.example.ExplicitProxy
```

To run the no-proxies version without a proxy (will time-out if running on a private subnet):

```
java -cp target/proxy-example-v1-1.0.0.jar com.chariotsolutions.example.NoProxy
```

To run the no-proxies version with the proxy server configured by system properties:

```
java -Dhttps.proxyHost="squid_proxy.internal" -Dhttps.proxyPort=3128 -Dhttp.nonProxyHosts=169.254.169.254 -cp target/proxy-example-v1-1.0.0.jar com.chariotsolutions.example.NoProxy
```

To run the no-proxies version with the proxy server configured by environment variables:

```
export HTTPS_PROXY=http://squid_proxy.internal:3128
java -cp target/proxy-example-v1-1.0.0.jar com.chariotsolutions.example.NoProxy
```


### Java version 2 SDK

To build:

```
mvn clean package
```

To run the explicit proxy version (will fail if you don't have a proxy server running,
with the DNS name `squid_proxy.internal`):

```
java -cp target/proxy-example-v1-1.0.0.jar com.chariotsolutions.example.ExplicitProxy
```

To run the no-proxies version without a proxy (will time-out if running on a private subnet):

```
java -cp target/proxy-example-v1-1.0.0.jar com.chariotsolutions.example.NoProxy
```

To run the no-proxies version with the proxy server configured by system properties:

```
java -Dhttp.proxyHost="squid_proxy.internal" -Dhttp.proxyPort=3128 -Dhttp.nonProxyHosts=169.254.169.254 -cp target/proxy-example-v1-1.0.0.jar com.chariotsolutions.example.NoProxy
```

At the present time, the V2 SDK doesn't support configuration by environment variable.


### JavaScript version 2 SDK

This uses NodeJS for the example; you must install Node and NPM before building.

To build:

```
npm install``

To run the explicit proxy version (as with other examples, you must have a proxy server
running at the address `squid_proxy.internal`):

```
node explicit_proxy.js
```

There is, to the best of my knowledge, no way to configure a proxy using environment
variables.


### JavaScript version 3 SDK

At this time, I do not believe there is any way to configure a proxy server with the
v3 JavaScript SDK. It uses a different client configuration structure than the v2 SDK.
