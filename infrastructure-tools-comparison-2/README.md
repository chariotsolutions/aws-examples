This project is another comparison of infrastructure management tools for AWS. It
demonstrates the use of Terraform modules and CDK constructs to produce multiple
SQS queues with a consistent configuration.

There are four implementations:

* [CloudFormation](CloudFormation/README.md), as a baseline.
* [CDK](CDK/README.md), showing the use of user-defined constructs.
* [CDK-2](CDK-2/README.md), an extension that creates a combined queue policy.
* [Terraform](Terraform/README.md), which uses an in-project module to create the queue
  and related objects.


## General Notes

To run, you must have the ability to create SQS queues and IAM policies.I strongly
recommend running in a "sandbox" account so that you won't interfere with operations.

Each variant lives in its own sub-directory, so that it can create artifacts without
interfering with the others (this is particularly important for Terraform and CDK).
The README for each variant describes how to run it.


## Resources Created

Each variant of this project creates the following resources:

* Threee "primary" queues, named `Foo`, `Bar`, and `Baz`.
* Thread "dead letter" queues, named `Foo-DLQ`, `Bar-DLQ`, and `Baz-DLQ`.
* A consumer and producer policy for each queue (named `SQS-Foo-Consumer`,
  `SQS-Foo-Producer`, and so on).
* An "application role" that references the producer policies for all queues.
* (CDK-2 only) A consumer and producer policy for the queues as a group, named
  `SQS-STACKNAME-Consumer` and `SQS-STACKNAME-Producer`.
