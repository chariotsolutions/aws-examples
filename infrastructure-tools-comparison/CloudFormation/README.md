This variant of the project uses CloudFormation by itself to create resources. It provides a
baseline against which the other tools can be compared.

I prefer to use the AWS Console for CloudFormation, because (1) it's easier to enter parameters,
and (2) when you're updating a stack you can see the changes that will happen before clicking OK.
However, if you want to use the CLI, here are the commands (replace `UserCreationExample` with
whatever stack name you want to use):

```
aws cloudformation create-stack --stack-name UserCreationExample --capabilities CAPABILITY_NAMED_IAM --template-body file://template.yml
```

And to delete the stack:

```
aws cloudformation delete-stack --stack-name UserCreationExample
```
