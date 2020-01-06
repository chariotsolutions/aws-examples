This variant of the project uses the AWS Cloud Development Kit (CDK) to create resources.

Before you can run this you need to install Node and NPM. The instructions to do this for
the most recent versions can be found [here](https://nodejs.org/en/download/).

Then, install CDK (for more information, read the [Getting Started](https://docs.aws.amazon.com/cdk/latest/guide/getting_started.html) tutorial):

```
npm install -g aws-cdk
```

Then, from within this directory, run the following commands:

```
npm install

cdk synth > template.yml
```

As with the CFNDSL example, this creates a CloudFormation template, and you can use the Console
or CLI to manage the stack. Alternatively, you can let CDK deploy the stack for you (it will use
the name `UsersAndGroupsStack`):

```
cdk deploy
```

And also destroy it:

```
cdk destroy
```
