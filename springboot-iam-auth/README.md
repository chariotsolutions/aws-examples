An example Sprint Boot program that uses [IAM authentication](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/UsingWithRDS.IAMDBAuth.html)
to retrieve a limited-use password when making a database connection.


## Prerequisites

* Install Maven and a Java JDK (not JRE) on your development computer.
* Create an RDS Postgres database that is [configured for IAM authentication](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/UsingWithRDS.IAMDBAuth.Enabling.html).
  [This CloudFormation template](src/cloudformation/rds_iam.yml) will do that.
* Ensure that you can connect to this database server from your development computer.
* Create a user in this server and grant it the `rds_iam` role (this role prevents prevents password-based
  authentication, so should not be attached to the database master user).
* Ensure that the IAM user that you'll use to run this program has the IAM permission `rds-db:connect` for
  the database instance.


## Running

Either set the environment variables `PGHOST`, `PGPORT`, `PGUSER`, and `PGDATABASE` or hard code your
database connection information in `application.properties`.

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

2020-08-07 16:20:49,363 INFO  [main] c.c.e.s.Application - Starting Application on kgregory with PID 20228 (/home/kgregory/Workspace/aws-examples/springboot-iam-auth/target/classes started by kgregory in /home/kgregory/Workspace/aws-examples/springboot-iam-auth)
2020-08-07 16:20:49,364 DEBUG [main] c.c.e.s.Application - Running with Spring Boot v2.2.1.RELEASE, Spring v5.2.1.RELEASE
2020-08-07 16:20:49,364 INFO  [main] c.c.e.s.Application - No active profile set, falling back to default profiles: default
2020-08-07 16:20:49,760 INFO  [main] c.c.e.s.Application - Started Application in 0.526 seconds (JVM running for 0.764)
2020-08-07 16:20:49,760 INFO  [main] c.c.e.springboot.Runner - application started
2020-08-07 16:20:49,768 DEBUG [main] c.c.e.s.d.IAMAuthDataSource - requesting IAM token for user example
2020-08-07 16:20:50,635 DEBUG [HikariPool-1 connection adder] c.c.e.s.d.IAMAuthDataSource - requesting IAM token for user example
2020-08-07 16:20:51,062 INFO  [main] c.c.e.springboot.Runner - database timestamp: 2020-08-07 16:20:51.041191
```

The last line shows that the program was able to connect to the database and execute a simple query.

Note that there are two requests for an IAM token: the first is triggered by the main program, as it performs
its query. The second is performed by a background thread that appears to be managed by HikariCP, for the
purpose of keeping an idle connection available in the pool (even though I've tiried to configure it to use
only one connection).


## Implementation

This project contains three Java classes:

* `Application` provides the `main()` method, which initializes the application context. It also provides the
  factory method to create the `spring.datasource` bean.
* `Runner` contains the actual application code. It is a Spring component, and is autowired with a `JdbcTemplate`
  instance (which is, in turn, autowired with the default datasource). It uses that object to execute a simple
  SQL command that retrieves the current time from the database server.
* `IAMAuthDataSource` is a custom subclass of `PGSimpleDataSource` class that overrides the `getConnection()`
  method to first retrieve a token (limited-use password) from IAM. It is not specific to this example, and
  in a typical development environment would be maintained as a shared dependency.

Because we use a custom datasource, we can't simply configure a URL in `application.properties`. And because
of that, Spring Boot won't know to use the HikariCP connection pool; it would assume that we want to use an
embedded datasource. We solve this problem by providing an explicit factory for the default datasource bean.

Using an explicit factory, which returns a typed implementation object, we can also make use of properties
exposed by that implementation in our application configuration. In the case of this example, I use the
`dataSourceClassName` and `dataSourceProperties` properties of `com.zaxxer.hikari.HikariDataSource` to
configure the underlying custom datasource.
