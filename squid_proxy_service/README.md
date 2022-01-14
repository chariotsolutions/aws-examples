This example deploys a Squid proxy to serve as a controlled path between AWS
applications and external services (including AWS). This can help to mitigate
remote-code execution vulnerabilities, by blocking connections to the attacker's
endpoint.

Squid is perhaps known as a cache server, which sits between users and the sites
they use, storing artifact (such as images) so that they don't need to be pulled
from the origin server whenever viewed. In this example, however, we use it as a
simple "forward" proxy, which sits between an application and the web sites that
it uses, and decides whether to allow the connection.

> Forward proxies have a bad reputation: an unsecured proxy that's accessible
  from the Internet can allow a user or program to access a website while hiding
  its actual origin. For this example, the proxy lives inside an AWS VPC, only
  accepts connections from within the VPC, and restricts the destinations for
  those connections.

We chose the Squid proxy because it is simple to configure for our needs (although
the [complete set of config directives](http://www.squid-cache.org/Doc/config/) is
quite large). Other options include Apache httpd and HAProxy; there's also a
third-party module for nginx. If you are more comfortable with a different server,
feel free to adapt this example to use it.


## Configuring the proxy

To configure a proxy, you start with [acl](http://www.squid-cache.org/Doc/config/acl/)
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

All of these examples use the hostname `squid_proxy.internal` to refer to the proxy. If
you changed the name when deploying, or your Cloud Map namespace uses a different DNS
name, change as needed.


### Python

Python provides you with two ways to configure a proxy: via environment variables or
with an explicit dictionary of proxy destinations. These mechanisms are available to
the Boto3 AWS SDK, and the [requests](https://docs.python-requests.org/en/master/)
library. The built-in `urllib` package also supports environment variables, but has
a different approach to explicitly-configured proxies.

I'll start with environment variables:

* `HTTP_PROXY` identifies the proxy server to use for HTTP requests.
* `HTTPS_PROXY` identifies the proxy server to use for HTTPS requests.

Both of these variables hold the URL of the server: `http://squid_proxy.internal:3128`.
They can also include a username and password for authenticated requests (which I don't
show here because the example proxy doesn't use authentication).

Environment variables simplify deployment, _but can't be used for programs running in
EC2 or ECS that use instance roles._ The reason is that the credentials associated
with these roles are retrieved using an HTTP request to the instance metadata endpoint.
This request will be passed to the proxy, which is unable to fulfill it.

Instead, you can use an explicit proxy dictionary:

```
proxies = {
  'http': 'http://squid_proxy.internal:3128',
  'https': 'http://squid_proxy.internal:3128',
}

boto_config = botocore.config.Config(proxies=proxies)

client = boto3.client('logs', config=boto_config)
```

This same dictionary can be used for calls through the `requests` library, either
on a per-request basis or attached to a `Session` object:

```
rsp = requests.get("http://www.example.com", proxies=proxies)

session = requests.Session()
session.proxies.update(proxies)

rsp = session.get("http://www.example.com")
```


### Jave version 1 SDK

The version 1 SDK provides several ways to configure a proxy:

* Environment variables.
* System properties.
* Explicit configuration.

I'll start with explicit configuration, since the it makes the other options
easier to understand.  To configure a proxy endpoint, you must provide a
`ClientConfiguration` object to the client builder:

```
ClientConfiguration config = new ClientConfiguration()
                             .withProxyProtocol(Protocol.HTTP)
                             .withProxyHost("squid-proxy.internal")
                             .withProxyPort(3128)
                             .withNonProxyHosts("169.254.169.254");

AWSLogs client = AWSLogsClientBuilder.standard()
                 .withClientConfiguration(config)
                 .build();
```

The `ClientConfiguration` object alows you to configure each aspect of the proxy
URL -- scheme, username, password, hostname, and port -- individually. A nice
feature of the Java SDK is the ability to tell the client to bypass the proxy for
specific hostnames: here I give it the EC2 metadata address, which means that I
can retrieve EC2 instance credentials. There are also functions for working with
Windows NTLM domain proxies.

As I said, the system properties are based on these client configuration methods,
and there are two sets of matched properties:

* `http.proxyHost` / `https.proxyHost` to set the hostname.
* `http.proxyPort` / `https.proxyPort` to set the port.
* `http.proxyUser` / `https.proxyUser` to set the (optional) username for an
  authenticating proxy.
* `http.proxyPassword` / `https.proxyPassword` to set the (optional) password
  for an authenticating proxy.

The system property used depends on the type of connection to AWS: if you use
an HTTP connection (which you shouldn't!), the client picks `http.proxyHost`
and its siblings; if you use an HTTPS connection (the default), it picks
`https.proxyHost` and siblings.

There's also a property `http.nonProxyHosts`, for setting hostnames that bypass
the proxy. There's _not_ a system property to choose the protocol, nor are there
system proxies for NTLM authentication.

To use these system proeprties, you would normally provide them when invoking
the Java application:

```
java -Dhttps.proxyHost="localhost" -Dhttps.proxyPort=3128 -Dhttp.nonProxyHosts=169.254.169.254 -jar myapp.jar
```

Passing these properties on the command-line is straightforward, although it
may be inconvenient. However, there's no way to set provide system properties
to a Lambda, so you must explicitly set them in your function code. This may
cause problems with order of initialization, since the Lambda runtime performs
initialization (such as logging) before it ever calls your function code.

Fortunately, the v1 SDK supports environment variables:

* `HTTP_PROXY` and `HTTPS_PROXY` act the same way that they do in Python
  (eg: `http://squid-proxy:3128` or `http://user:password@otherproxy:9999`).
* `NO_PROXY` contains a list of the hostnames that should bypass the proxy.
