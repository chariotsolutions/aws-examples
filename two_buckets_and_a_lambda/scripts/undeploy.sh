#!/bin/bash
################################################################################################
##
## Undeployes the example: removes all buckets (which may contain content) and then destroys
## the CloudFormation stack. Must be run using appropriate IAM permissions.
##
## Invocation:
##
##      undeploy.sh STACK_NAME BASE_BUCKET_NAME
##
## Where:
##
##      STACK_NAME       is the name of the deployed stack, unique within the current region
##      BASE_BUCKET_NAME is used to construct the names of the three staging buckets. This
##                       must be unique across AWS.
##
## Note: you must have the AWS CLI installed for this script to work.
##
################################################################################################

if [[ $# -ne 2 ]] ; then
    echo "invocation: undeploy.sh STACK_NAME BASE_BUCKET_NAME"
    exit 1
fi

STACK_NAME=$1
BASE_BUCKET_NAME=$2

ARCHIVE_BUCKET_NAME="${BASE_BUCKET_NAME}-archive"
STATIC_BUCKET_NAME="${BASE_BUCKET_NAME}-static"
UPLOADS_BUCKET_NAME="${BASE_BUCKET_NAME}-uploads"


echo ""
echo "deleting all buckets"
echo ""

aws s3 rb s3://${ARCHIVE_BUCKET_NAME} --force
aws s3 rb s3://${STATIC_BUCKET_NAME} --force
aws s3 rb s3://${UPLOADS_BUCKET_NAME} --force


echo ""
echo "deleting CloudFormation stack"
echo ""

aws cloudformation delete-stack --stack-name ${STACK_NAME} 


echo ""
echo "waiting for stack deletion to finish (should be only a few minutes)"
echo ""

aws cloudformation wait stack-delete-complete --stack-name ${STACK_NAME}
