An example of using a Docker container to build and deploy Lambdas.

For more information, see [this blog post]().


## Building the Docker image

The `docker` directory contains the configuration files -- Dockerfile and Makefile -- used for
this example.

```
docker build -t build-environment:latest docker/
```


## Creating an empty Lambda

The empty Lambda, along with its log stream and security group, are created using CloudFormation, from the
template `cloudformation.yml`. Create using the AWS Console or
[this utility script](https://github.com/kdgregory/aws-misc/blob/trunk/utils/cf-runner.py).

The template uses the name "Example" for this Lambda. You can change the name via a template
parameter, but beware that you'll have to use the changed name in the next step.


## Building and deploying the actual Lambda

To just build the Lambda, storing its bundle in the current directory:

```
docker run --rm --user $(id -u):$(id -g) -v $(pwd):/build -e DEPLOY_DIR=/build build-environment:latest

```

If you want to both build and deploy, you must provide the container with AWS credentials. The easiest
way to do that is to define and pass environment variables:

```
docker run --rm -v $(pwd):/build -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -e AWS_DEFAULT_REGION build-environment:latest deploy
```
