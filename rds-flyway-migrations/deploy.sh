# Use with: ./deploy.sh stackname region
aws cloudformation deploy --stack-name $1 --region $2 --capabilities CAPABILITY_NAMED_IAM --template-file cloudformation.yml
