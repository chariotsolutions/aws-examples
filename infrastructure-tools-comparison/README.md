This project compares CloudFormation, Terraform, CFNDSL, and CDK as tools for managing users,
groups, and roles. Each variant is in its own sub-directory, and creates the following resources:

* Three users: `user1`, `user2`, and `user3`.
* Two groups: `group` and `group2`, which have permissions to assume specific roles.

The assumable roles aren't defined by this example. I use names such as `FooAppDeveloperRole` and
`FooAppReadOnlyRole` to represent the sorts of user-assumable roles that would allow management
of an application Foo in the developer account, but read-only access in the production account.


# General Notes

To run, you must have the ability to create users, groups, and policies (essentially, admin-level
rights).  I recommend running in a "sandbox" account so that you won't interfere with operational
users/groups.

Each variant lives in its own sub-directory, so that it can create artifacts without interfering
with the others (this is particularly important for Terraform and CDK). The instructions below
assume that you're running from the relevant directory.


# BasicUserPolicy

All of the scripts expect an existing managed policy named `BasicUserPolicy`, which will be assigned
to each created user.

Here is the policy that we use in our sandbox account; it allows users to retrieve information about
themselves, change their own passwords, assign a virtual MFA device, and manage the keys that they
use to interact with AWS services.

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "",
            "Effect": "Allow",
            "Action": [
                "iam:UploadSSHPublicKey",
                "iam:UpdateSSHPublicKey",
                "iam:UpdateAccessKey",
                "iam:List*",
                "iam:Get*",
                "iam:EnableMFADevice",
                "iam:DeleteSSHPublicKey",
                "iam:DeleteAccessKey",
                "iam:CreateAccessKey",
                "iam:ChangePassword"
            ],
            "Resource": "arn:aws:iam::*:user/${aws:username}"
        },
        {
            "Sid": "",
            "Effect": "Allow",
            "Action": "iam:DeleteVirtualMFADevice",
            "Resource": "arn:aws:iam::*:mfa/${aws:username}"
        },
        {
            "Sid": "",
            "Effect": "Allow",
            "Action": [
                "iam:ListVirtualMFADevices",
                "iam:CreateVirtualMFADevice"
            ],
            "Resource": "*"
        }
    ]
}
```


# CloudFormation

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


# Terraform

Creating the resources is a two-step process:

```
terraform init
```

Which will download the AWS provider, and


```
terraform apply
```

Which performs the infrastructure changes. You will have to manually approve making this changes.

It may turn into a three-step process: sometimes the users or groups aren't ready to have roles applied,
and you see an error about the resource not existing. Running `terraform apply` a second time resolves
this.

To destroy the resources:

```
terraform destroy
```

Note that the `.gitignore` file explicitly excludes the `tfstate` files. This is not something that
you'd want to do in a real deployment; those files should be checked-in alongside the template.


# CFNDSL

You first need to install CFNDSL per the instructions [here](https://www.rubydoc.info/gems/cfndsl)
(and you may also need to install a compatible Ruby version as well).

Then, generate the template using this command:

```
cfndsl --disable-binding -f yaml script.rb > template.yml
```

* `--disable-binding` suppresses a warning about locally-defined configuration.
  In normal use, you would provide the lists of users, groups, &c via external
  configuration files.
* `-f yaml` specifies that the output should be [YAML](https://yaml.org/).
  Omit to generate JSON (in which case you probably want to add `-p`, for
  pretty-printing).

Once you have the template, you can use the AWS Console or the CloudFormation instructions above
to create and destroy the stack.


# CDK

First step is to install Node and NPM. The instructions to do this for the most recent
versions can be found [here](https://nodejs.org/en/download/).

Next, install CDK (for more information, read the [Getting Started](https://docs.aws.amazon.com/cdk/latest/guide/getting_started.html) tutorial).

```
npm install -g aws-cdk
```

From within the directory, run the following commands:

```
npm install

cdk synth > template.yml
```

As with the CFNDSL example, this creates a CloudFormation template. You can then use the Console
or CLI to manage the stack. Alternatively, you can let CDK deploy the stack (which will ask you
to confirm changes):

```
cdk deploy
```

And destroy it:

```
cdk destroy
```
