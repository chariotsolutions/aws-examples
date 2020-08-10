An example Sprint Boot program that uses the [AWS Labs Secrets Manager JDBC driver](https://github.com/aws/aws-secretsmanager-jdbc)
to connect to an RDS database.


## Prerequisites

* Install Maven and a Java JDK (not JRE) on your development computer.
* Create an RDS Postgres database, along with a Secrets Manager secret that identifies a user
  in that database. [This CloudFormation template](src/cloudformation/rds_secretsmanager.yml)
  will do that, with the database master user stored in the secret.
* Ensure that you can connect to this database server from your development computer.


## Running

Set the environment variables `PGHOST`, `PGPORT`, and `PGDATABASE` to reference your database
instance and the environment variable `SECRET_NAME` to the name or ARN of the secret holding
the username and password.

From the project root directory, execute `mvn spring-boot:run`.

After the messages from Maven as it builds the project, you should see output like the following:

```
  .   ____          _            __ _ _
 /\\ / ___'_ __ _ _(_)_ __  __ _ \ \ \ \
( ( )\___ | '_ | '_| | '_ \/ _` | \ \ \ \
 \\/  ___)| |_)| | | | | || (_| |  ) ) ) )
  '  |____| .__|_| |_|_| |_\__, | / / / /
 =========|_|==============|___/=/_/_/_/
 :: Spring Boot ::        (v2.2.1.RELEASE)

2020-08-07 16:22:27,877 INFO  [main] c.c.e.s.Application - Starting Application on kgregory with PID 20364 (/home/kgregory/Workspace/aws-examples/springboot-secman-auth/target/classes started by kgregory in /home/kgregory/Workspace/aws-examples/springboot-secman-auth)
2020-08-07 16:22:27,878 DEBUG [main] c.c.e.s.Application - Running with Spring Boot v2.2.1.RELEASE, Spring v5.2.1.RELEASE
2020-08-07 16:22:27,878 INFO  [main] c.c.e.s.Application - No active profile set, falling back to default profiles: default
2020-08-07 16:22:28,483 INFO  [main] c.c.e.s.Application - Started Application in 0.752 seconds (JVM running for 0.996)
2020-08-07 16:22:28,483 INFO  [main] c.c.e.springboot.Runner - application started
2020-08-07 16:22:29,397 INFO  [main] c.c.e.springboot.Runner - database timestamp: 2020-08-07 16:22:29.380214
```

The last line shows that the program was able to connect to the database and execute a simple query.


## Implementation

This is a simple Spring Boot application consisting of two classes:

* `Application` provides the `main()` method, which initializes the application context. In a more complex example
  it would also provide bean factory methods.
* `Runner` contains the actual application code. It is a Spring component, and is autowired with a `JdbcTemplate`
  instance (which is, in turn, autowired with the default datasource). It uses that object to execute a simple
  SQL command that retrieves the current time from the database server.

The application configuration file configures the default datasource, and also explicitly tells Spring Boot that
this is _not_ a web-application.
