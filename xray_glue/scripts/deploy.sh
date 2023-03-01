#!/bin/bash
################################################################################
##
## This script creates a bucket, uploads data into it, and uses a CloudFormation
## stack to deploy example jobs along with an X-Ray daemon.
##
## Invocation:
##
##    deploy.sh BUCKET_NAME STACK_NAME
##
## Where:
##
##    BUCKET_NAME   is used to hold Glue job scripts, as well as for the source
##                  and destination of those scripts.
##    STACK_NAME    is the name of the stack to create with CloudFormation.
##
################################################################################


if [[ $# -ne 2 ]] ; then
    echo "invocation: deploy.sh BUCKET_NAME STACK_NAME"
    exit 1
fi

BUCKET_NAME=$1
STACK_NAME=$2


##
## Create bucket and upload content
##

SCRIPT_PREFIX="jobs"
DATA_PREFIX="json"
DEST_PREFIX="avro"

aws s3 mb s3://${BUCKET_NAME}
if [[ $? -ne 0 ]] ; then
    echo "failed to create bucket"
    exit 2
fi

for f in jobs/*.py
do
    aws s3 cp $f s3://${BUCKET_NAME}/${SCRIPT_PREFIX}/$(basename $f)
done

for f in $(find data -name *.json)
do 
    aws s3 cp $f s3://${BUCKET_NAME}/${f/data/$DATA_PREFIX}
done

##
## Create CloudFormation stack
##

cat > /tmp/$$.cfparams <<EOF
[
  {
    "ParameterKey":     "BucketName",
    "ParameterValue":   "${BUCKET_NAME}"
  },
  {
    "ParameterKey":     "ScriptPrefix",
    "ParameterValue":   "${SCRIPT_PREFIX}"
  },
  {
    "ParameterKey":     "DataPrefix",
    "ParameterValue":   "${DATA_PREFIX}"
  },
  {
    "ParameterKey":     "OutputPrefix",
    "ParameterValue":   "${DEST_PREFIX}"
  }
]
EOF

aws cloudformation create-stack \
                   --stack-name ${STACK_NAME} \
                   --template-body file://scripts/jobs.yml \
                   --capabilities CAPABILITY_NAMED_IAM \
                   --timeout-in-minutes 30 \
                   --parameters "$(< /tmp/$$.cfparams)"

# this should never happen unless you modify the template
if [[ $? -ne 0 ]] ; then
    echo "failed to create stack"
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
