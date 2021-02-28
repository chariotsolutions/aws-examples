FROM amazon/aws-lambda-python:3.8

RUN yum install -y make zip

RUN pip install awscli

COPY Makefile /

WORKDIR /build

ENV DEPLOY_DIR=/tmp/deploy

ENTRYPOINT ["/usr/bin/make", "--environment-overrides", "--directory=/build", "--makefile=/Makefile"]
