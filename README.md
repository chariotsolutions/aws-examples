This repository contains examples of AWS-related topics, typically examples from
Chariot's [blog](https://chariotsolutions.com/blog/).  All code is licensed under
[Apache 2.0](https://www.apache.org/licenses/LICENSE-2.0).

Each sub-directory is a distinct project, with a README that describes the project
in more detail:

* [cloudtrail_to_elasticsearch](cloudtrail_to_elasticsearch)

  A Lambda that uploads CloudTrail events to an Elasticsearch cluster. Referenced by
  [Delving into CloudTrail Events](https://chariotsolutions.com/blog/post/delving-into-cloudtrail-events/).

* [infrastructure-tools-comparison](infrastructure-tools-comparison)

  Examples for creating users, groups, and roles using CloudFormation, Cloud Development
  Kit (CDK), CFNDSL, and Terraform. Referenced by
  [Comparing Infrastructure Tools: A First Look at the AWS Cloud Development Kit)(https://chariotsolutions.com/blog/post/comparing-infrastructure-tools-a-first-look-at-the-aws-cloud-development-kit/).

* [infrastructure-tools-comparison-2](infrastructure-tools-comparison-2)

  Comparison of Terraform modules and CDK custom constructs. This is a follow-on to
  the prior example.

* [lambda_build_in_docker](lambda_build_in_docker)

  A skeleton Python Lambda that depends on the `psycopg2` database library. Referenced by
  [Building and Deploying Lambdas from a Docker Container](https://chariotsolutions.com/blog/post/building-and-deploying-lambdas-from-a-docker-container/).

* [lambda_container_images](lambda_container_images)

  A skeleton Lambda that depends on the `psycopg2` database library and is deployed as a
  Docker container. Referenced by [Getting Started with Lambda Container Images](https://chariotsolutions.com/blog/post/getting-started-with-lambda-container-images/).

* [sandbox-policies](sandbox-policies)

  IAM and service control policies that Chariot uses for managing developer sandboxes. Referenced by
  [Building Developer Sandboxes on AWS](https://chariotsolutions.com/blog/post/building-developer-sandboxes-on-aws/).

* [springboot-secman-auth](springboot-secman-auth) / [springboot-iam-auth](springboot-iam-auth)

  Examples of using connection-time credentials with Spring Boot. The first uses an AWSLabs 
  driver library to retrieve credentials from Secrets Manager. The second uses a custom
  Postgres datasource implementation to retrieve IAM-generated credentials. Referenced by
  _RDS Database Authentication with Spring Boot_, parts 
  [one](https://chariotsolutions.com/blog/post/rds-database-authentication-with-spring-boot-part-1-secrets-manager/)
  and [two](https://chariotsolutions.com/blog/post/rds-database-authentication-with-spring-boot-part-2-iam-authentication/).

* [two_buckets_and_a_lambda](two_buckets_and_a_lambda)

  A Lambda-based application that allows users to upload files from a browser (showing two ways
  to accomplish them) and then process those files via a triggered Lambda. Referenced by
  [Two Buckets and a Lambda: a pattern for file processing](https://chariotsolutions.com/blog/post/two-buckets-and-a-lambda-a-pattern-for-file-processing/).

* [untagged_ec2_cleanup](untagged_ec2_cleanup)

  A Lambda that will find EC2 instances that don't have the proper ownership tags and shutting
  them down. Referenced by
  [Building Developer Sandboxes on AWS](https://chariotsolutions.com/blog/post/building-developer-sandboxes-on-aws/).
