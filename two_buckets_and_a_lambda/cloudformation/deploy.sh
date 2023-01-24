#!/bin/bash
################################################################################################
##
## Deploys the example: creates the CloudFormation stack, waits for it to be ready, and then
## uploads the Lambdas and static content. Must be run using appropriate IAM permissions.
##
## Invocation:
##
##      deploy.sh STACK_NAME BASE_BUCKET_NAME
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
    echo "invocation: deploy.sh STACK_NAME BASE_BUCKET_NAME"
    exit 1
fi

STACK_NAME=$1
BASE_BUCKET_NAME=$2

ARCHIVE_BUCKET_NAME="${BASE_BUCKET_NAME}-archive"
STATIC_BUCKET_NAME="${BASE_BUCKET_NAME}-static"
UPLOADS_BUCKET_NAME="${BASE_BUCKET_NAME}-uploads"


function retrieve_output_value
{
    aws cloudformation describe-stacks --stack-name ${STACK_NAME} --output text --query "Stacks[].Outputs[?OutputKey=='$1'].OutputValue" ;
}


echo ""
echo "creating CloudFormation stack"
echo ""

cat > /tmp/cfparams.$$ <<EOF
[
  {
    "ParameterKey":     "ArchiveBucketName",
    "ParameterValue":   "${ARCHIVE_BUCKET_NAME}"
  },
  {
    "ParameterKey":     "StaticBucketName",
    "ParameterValue":   "${STATIC_BUCKET_NAME}"
  },
  {
    "ParameterKey":     "UploadBucketName",
    "ParameterValue":   "${UPLOADS_BUCKET_NAME}"
  }
]
EOF

aws cloudformation create-stack \
                   --stack-name ${STACK_NAME} \
                   --template-body file://cloudformation.yml \
                   --capabilities CAPABILITY_NAMED_IAM \
                   --timeout-in-minutes 30 \
                   --parameters "$(< /tmp/cfparams.$$)"

# this should never happen unless you modify the template
if [[ $? -ne 0 ]] ; then
    echo "Stack failed to create"
    exit 2
fi


echo ""
echo "waiting for stack creation to finish (should only take a few minutes)"
echo ""

# this sleep ensures that the stack can be accessed by name
sleep 10

# it would be really nice if this command gave some feedback
aws cloudformation wait stack-create-complete --stack-name ${STACK_NAME}

# because it can run for a half hour before failing
if [[ $? -ne 0 ]] ; then
    echo "Stack failed to create"
    exit 2
fi


echo ""
echo "copying static content"
echo ""

aws s3 cp ../static/index.html s3://${STATIC_BUCKET_NAME}/index.html               --acl public-read --content-type 'text/html; charset=utf-8'
aws s3 cp ../static/js/signed-url.js s3://${STATIC_BUCKET_NAME}/js/signed-url.js   --acl public-read --content-type 'text/javascript'
aws s3 cp ../static/js/credentials.js s3://${STATIC_BUCKET_NAME}/js/credentials.js --acl public-read --content-type 'text/javascript'


echo ""
echo "deploying Lambda code"
echo ""

## note: at this point each Lambda is in a single file and doesn't have dependencies; if we ever add dependencies we'll
## need a fancier deployment (ie, a Makefile)

rm -f /tmp/$$.zip ; zip -q /tmp/$$.zip -j ../lambda/processor.py
aws lambda update-function-code --function-name $(retrieve_output_value ProcessorLambdaName) --zip-file fileb:///tmp/$$.zip &>> /tmp/$$.log

rm -f /tmp/$$.zip ; zip -q /tmp/$$.zip -j ../lambda/credentials.py
aws lambda update-function-code --function-name $(retrieve_output_value CredentialsLambdaName) --zip-file fileb:///tmp/$$.zip &>> /tmp/$$.log

rm -f /tmp/$$.zip ; zip -q /tmp/$$.zip -j ../lambda/signed_url.py
aws lambda update-function-code --function-name $(retrieve_output_value SignedUrlLambdaName) --zip-file fileb:///tmp/$$.zip &>> /tmp/$$.log


echo ""
echo "endpoint: " $(retrieve_output_value APIGatewayUrl)
echo ""
