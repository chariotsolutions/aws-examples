# Aurora Serverless Data API Example

This is an implementation of the Lambda described [in this blog post](https://chariotsolutions.com/blog/post/serverless-databasing-with-the-aurora-data-api/).

It uses the Data API to update a user's email preferences in response to an
"unsubscribe" notification from an email provider (using the message format of
the [Twilio SendGrid](https://docs.sendgrid.com/for-developers/tracking-events/event#events)
webhook).


## Deploying

Deploying this Lambda is a multi-step process:

1. Create a CloudFormation stack from the template `cloudformation.yml`. This
   stack includes an HTTP Gateway and Aurora Serverless database cluster, in
   addition to a "dummy" Lambda.

   The stack has two parameters:

   * `VpcId`: VPC where the database will be deployed.
   * `SubnetIds`: subnets where the database will be deployed. Provide at least two.

   And it provides the following outputs:

   * `APIGatewayUrl`: the endpoint called by the webhook.
   * `DatabaseSecretArn`: the ARN of the secret holding the database connection
     information. This is needed to run the `init_database.py` script.
   * `DatabaseInstanceArn`: the ARN of the Aurora Serverless cluster. This is
     also needed to run the `init_database.py` script.

   *Beware:* you will incur AWS usage charges for this example. They should be
   minimal (on the order of a few cents), but don't forget to delete the stack
   when you're done.

2. Run the script `init_database.py` to create the database table and add
   sample users. You must provide the two ARNs from the stack outputs. The
   script creates three default users, corresponding to the records in the
   sample event. If you want to create more users (for example, to try
   your own events), pass their email addresses as command-line arguments:

   ```
   ./init_database.py SECRET_ARN DATABASE_ARN me@example.com you@example.com ...
   ```

   You will need to have Python 3 installed to run this script, along with the
   `boto3` library and its dependencies. If you've already installed the AWS
   command-line program (`awscli`), these will be present.

   Note that this script also uses the Data API to perform its actions.

3. Use the Console to replace the source code of the Lambda with the contents
   of the file `lambda.py`. 


## Running

To see the current email status of your users, run the following query in the
[Console Query Editor](https://console.aws.amazon.com/rds/home#query-editor:):

```
select * from EMAIL_PREFERENCES
```

After running `init_database.py`, you should see some number of users, all of
which have a `MARKETING_OPT_IN` value of `true`.

Now, use `curl` to upload the sample event:

```
curl -X POST -d @example_notifications.json API_GATEWAY_ENDPOINT
```

After this, you can re-run the query, and you should see that `user2@example.com`
and `user3@example.com` have a `MARKETING_OPT_IN` value of `false`.
