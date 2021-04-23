An example of building and using a Lambda Container Image.

There are directories in this project:

* `lambda` contains the Lambda source code, `requirements.txt`, and a Dockerfile to
  produce the container image.

* `cloudformation` contains templates to create an ECR repository and a Lambda that
  depends on on the images it holds. See below for usage.

* `terraform` contains two Terraform projects: one to create the ECR repository, and
  one to create a Lambda that depends on it. See below for usage.

To deploy (all code examples start from the project root directory):

1. Use either Terraform or CloudFormation to create the ECR repository. The default
   name for this repository is `lambda_container`; you can provide a different name,
   but will have to use that name below. You can also create the repository manually,
   but will need to grant permissions to Lambda.

   ```
   cd cloudformation

   aws cloudformation create-stack --stack-name LambdaContainerExample-ECR --template-body file://`pwd`/cloudformation-ecr.yml
   ```

   _or_

   ```
   cd terraform/ecr

   terraform init

   terraform apply
   ```


2. Build the image. The name that you give to the image doesn't matter, since you'll tag
   it before pushing to the repository.

   ```
   cd lambda

   docker build -t container-example:latest .
   ```

3. Tag and upload the image. You can get the actual push instructions from the ECR repository, or
   replace the account number (123456789012), region (us-east-1), and image name (container_example)
   in the commands below below. Note that you will need permission to push to the repository.

   ```
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com

   docker tag container-example:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/container-example:latest

   docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/container-example:latest
   ```

1. Use either Terraform or CloudFormation to deploy the Lambda. The default name for the
   Lambda is `LambdaContainerExample`, and the default name for the ECR repository is
   `lambda_container`. If you changed the name in step 1, you'll also need to change it
   here. Note that this step also creates an execution role for the Lambda, named after
   the Lambda but with `-REGION-execution` appended (where `REGION` is the AWS region
   where you're deploying).

   ```
   cd cloudformation

   aws cloudformation create-stack --stack-name LambdaContainerExample --capabilities CAPABILITY_NAMED_IAM  --template-body file://`pwd`/cloudformation-lambda.yml
   ```

   _or_

   ```
   cd terraform/lambda

   terraform init

   terraform apply
   ```

5. Delete the example resources

   If you do not do this, you will incur charges for the repository. Unfortunately,
   CloudFormation can't delete a repository that has images in it, so you'll need
   to go into the Console and delete it manually. Then, depending on whether you
   used CloudFormation or Terraform:

   ```
   aws cloudformation delete-stack --stack-name LambdaContainerExample

   aws cloudformation delete-stack --stack-name LambdaContainerExample-ECR
   ```

   _or_

   ```
   cd terraform/lambda

   terraform destroy

   cd ../ecr

   terraform destroy
   ```

   Note: if you don't manually delete the images, CloudFormation will be unable to delete
   the repository.
