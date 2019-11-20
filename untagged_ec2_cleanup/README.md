# Untagged EC2 Cleanup

This is an example Lambda function that will identify EC2 instances that don't meet all
of the following requirements:

* A non-empty `Name` tag
* A non-empty `CreatedBy` tag
* Either created within the past 7 days, or has a `DeleteAfter` tag that specifies a future
  date in the format `YYYY-MM-DD`,

This Lambda is intended to be run against sandbox accounts, to ensure that developers don't
start machines and forget about them. It is typically triggered via a scheduled CloudWatch Event.


## Deployment

This function is deployed using a CloudFormation template that creates the following resources:

* The Lambda function itself.
* An execution role.
* A CloudWatch Events rule that triggers the function.

To create the stack, you must provide the following parameters:

* `FunctionName`  
  The name of the Lambda function. This is also used as the base name for the function's
  execution role and trigger.
* `Accounts`  
  A comma-separated list of the accounts to be examined.
* `Regions`  
  A comma-separated list of the regions to examine for those accounts. This defaults to the
  US regsions.
* `RoleName`  
  The name of a role that is present in all accounts and has permissions to examine and terminate
  EC2 instances. This defaults to `OrganizationAccountAccessRole`, which is the default admin role
  created when adding an account to an organization.
* `Schedule`  
  The CloudWatch Events schedule rule that will trigger the Lambda. This defaults to a CRON
  expression for 4 AM UTC.

**As created, the trigger is disabled and the `terminate()` call is commented-out in the Lambda.**

Before enabling, you should run the Lambda and verify from its output that it will not delete any
unexpected instances. You can either run manually, using the "Test" feature from the AWS Console
(any test event is fine; it's not used), or enable the trigger and examine the CloudWatch logs for
the function after it runs.

When you are ready to run for real, uncomment the `instance.terminate()` call at line 45.
