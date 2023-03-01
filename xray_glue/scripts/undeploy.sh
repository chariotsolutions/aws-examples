#!/bin/bash
################################################################################
##
## This script force-destroys the bucket created by deploy.sh, along with the
## CloudFormation stack that creates Glue jobs and the X-Ray daemon.
##
## Invocation:
##
##    undeploy.sh BUCKET_NAME STACK_NAME
##
## Where:
##
##    BUCKET_NAME   is the bucket used for Glue scripts and data.
##    STACK_NAME    is the stack that creates the Glue jobs and X-Ray daemon.
##
################################################################################


if [[ $# -ne 2 ]] ; then
    echo "invocation: undeploy.sh BUCKET_NAME STACK_NAME"
    exit 1
fi

BUCKET_NAME=$1
STACK_NAME=$2

##
## Delete the bucket -- must happen first or CloudFormation will fail
##

aws s3 rb s3://${BUCKET_NAME} --force
if [[ $? -ne 0 ]] ; then
    echo "*** unable to delete bucket; tear down manually ***"
    exit 2
fi

##
## Then delete the stack
##

echo "deleting CloudFormation stack"
aws cloudformation delete-stack --stack-name ${STACK_NAME} 
