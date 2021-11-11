#!/usr/bin/env python3
""" Creates the example database table and populates sample users.

    Invocation:

        ./init_database.py SECRET_ARN DATABASE_ARN [ EXTRA_USER ...]

    Where:

        SECRET_ARN      is the ARN of the secret holding login credentials for the DB superuser.
        DATABASE_ARN    is the ARN of the datatabase cluster itself.
        EXTRA_USER      is zero or more email addresses, which will be added as users.

    Note: SECRET_ARN and DATABASE_ARN are exposed as outputs on the CloudFormation stack.
    """


import boto3
import sys
import uuid

from datetime import datetime


def execute(client, secret_arn, db_arn, sql, params=None):
    """ A generic method to execute statements that don't return data.
        """
    kw_args = {
        'secretArn':    secret_arn,
        'resourceArn':  db_arn,
        'sql':          sql,
    }
    if params:
        kw_args['parameters'] = params
    client.execute_statement(**kw_args)


def create_table(client, secret_arn, db_arn):
    print(f"creating table")
    execute(client, secret_arn, db_arn, 
            """
            create table if not exists EMAIL_PREFERENCES
            (
                user_id             text        not null primary key,
                email_address       text        not null,
                marketing_opt_in    boolean     not null default false,
                updated_at          timestamp   not null
            )
            """)
    print(f"creating index on EMAIL_ADDRESS")
    execute(client, secret_arn, db_arn,
            """
            create unique index EMAIL_PREFERENCES_IDX_ADDRESS on EMAIL_PREFERENCES(EMAIL_ADDRESS)
            """)


def insert_user(client, secret_arn, db_arn, email_address):
    print(f"inserting user: {email_address}")
    execute(client, secret_arn, db_arn, 
            """
            insert into EMAIL_PREFERENCES ( USER_ID, EMAIL_ADDRESS, MARKETING_OPT_IN, UPDATED_AT )
            values ( :user_id, :email_address, :marketing_opt_in, :updated_at )
            """,
            [
                {
                    'name':     'user_id',
                    'value':    {'stringValue': str(uuid.uuid4())}
                },
                {
                    'name':     'email_address',
                    'value':    {'stringValue': email_address}
                },
                {
                    'name':     'marketing_opt_in',
                    'value':    {'booleanValue': True}
                },
                {
                    'name':     'updated_at',
                    'typeHint': 'TIMESTAMP',
                    'value':    {'stringValue': datetime.now().isoformat(sep=' ', timespec='seconds')}
                }
            ])


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    secret_arn = sys.argv[1]
    db_arn = sys.argv[2]
    client = boto3.client('rds-data')
    create_table(client, secret_arn, db_arn)
    insert_user(client, secret_arn, db_arn, "user1@example.com")
    insert_user(client, secret_arn, db_arn, "user2@example.com")
    insert_user(client, secret_arn, db_arn, "user3@example.com")
    for extra_user in sys.argv[3:]:
        insert_user(client, secret_arn, db_arn, extra_user)
