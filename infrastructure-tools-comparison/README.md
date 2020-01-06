This project is a companion for [a blog post](https://chariotsolutions.com/blog/post/comparing-infrastructure-tools-a-first-look-at-the-aws-cloud-development-kit/)
comparing various infrastructure management tools for AWS. As an example, it creates a set of
users, groups, and roles as describe in [this blog post](https://chariotsolutions.com/blog/post/managing-aws-users-and-roles-in-a-multi-account-organization/).

The four tools that I compare are:

* [CloudFormation](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/Welcome.html), the AWS standard for declarative infrastructure.
* [CFNDSL](https://www.rubydoc.info/gems/cfndsl), a Ruby gem that allows generating CloudFormation templates programmatically.
* [CDK](https://docs.aws.amazon.com/cdk/latest/guide/home.html), an AWS-supported open-source project for generating and deploying CloudFormation templates.
* [Terraform](https://www.terraform.io/), the leading non-AWS contender for managing infrastructure declaratively.


## General Notes

To run, you must have the ability to create users, groups, and policies (essentially, admin-level
rights).  I strongly recommend running in a "sandbox" account so that you won't interfere with
operational users/groups.

Each variant lives in its own sub-directory, so that it can create artifacts without interfering
with the others (this is particularly important for Terraform and CDK). Each variant has a README
that describes how to run it:

* [CloudFormation](CloudFormation/README.md)
* [CFNDSL](CFNDSL/README.md)
* [CDK](CDK/README.md)
* [Terraform](Terraform/README.md)


## Resources Created

Each variant of this project creates the following resources:

* Three users: `user1`, `user2`, and `user3`.
* Two groups: `group` and `group2`, which have permissions to assume specific roles.

It does _not_ create the various IAM roles referenced by the group policies, as that's beyond
the scope of the example (and the roles don't need to exist to be referenced).

It also does _not_ create a managed policy named `BasicUserPolicy`, even though that policy
must exist for the users to be successfully created. For demonstration purposes, you can
create a policy with no permissions. If you'd like to use a real policy, here's the one we
use for our sandbox accounts:


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
