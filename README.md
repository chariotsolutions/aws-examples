This repository contains examples of AWS-related topics, typically supporting Chariot's
[blog](https://chariotsolutions.com/blog/). All code is licensed under Apache 2.0.

* `cloudtrail_to_elasticsearch` 

  A Lambda that uploads CloudTrail events to an Elasticsearch cluster. Referenced by
  [Delving into CloudTrail Events](https://chariotsolutions.com/blog/post/delving-into-cloudtrail-events/).

* `infrastructure-tools-comparison` 

  Examples for creating users, groups, and roles using CloudFormation, Cloud Development
  Kit (CDK), CFNDSL, and Terraform. Referenced by
  [Comparing Infrastructure Tools: A First Look at the AWS Cloud Development Kit)(https://chariotsolutions.com/blog/post/comparing-infrastructure-tools-a-first-look-at-the-aws-cloud-development-kit/).

* `infrastructure-tools-comparison-2` 

  Examples of using Terraform modules and CDK custom constructs.

* `sandbox-policies` 

  IAM and service control policies for managing developer sandboxes. Referenced by
  [Building Developer Sandboxes on AWS](https://chariotsolutions.com/blog/post/building-developer-sandboxes-on-aws/).

* `springboot-iam-auth`  
  `springboot-secman-auth`

  Examples of using connection-time credentials with Spring Boot. The former uses a custom
  Postgres datasource implementation to retrieve IAM-generated credentials, the latter uses
  an AWSLabs driver library to retrieve credentials from Secrets Manager.


* `untagged_ec2_cleanup` 

  A Lambda that will find EC2 instances that don't have the proper ownership tags and shutting
  them down. Referenced by
  [Building Developer Sandboxes on AWS](https://chariotsolutions.com/blog/post/building-developer-sandboxes-on-aws/).
