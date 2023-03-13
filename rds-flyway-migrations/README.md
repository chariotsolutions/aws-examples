# RDS Flyway Migrations Sample

This sample project creates an RDS instance within the private subnet of a VPC, and installs a CodeBuild project to run Flyway database migrations to provision the database.

Setup steps:

1. Install AWS CLI
2. Access an AWS account with rights to create an RDS instance, VPC, and create and run CodeBuilds.
3. Run the deploy.sh script - two positional parameters are
  - the name of the stack to create
  - the region to create your stack within
  
  - Example:
    ```bash
    ./deploy.sh rds-flyway-migrations us-east-2
    ```
4. Run the project created within CodeBuild to perform the migrations
5. Observe the logs to see that the environment variables for the username, database name and password are not exposed to the logs
6. You may also use the RDS control panel to perform queries against the database


