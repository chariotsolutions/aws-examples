/* New table for application users */
create table user_accounts (
    id uuid primary key default gen_random_uuid(),
    cognito_id varchar not null,
    email_address varchar not null,
    first_name varchar not null,
    last_name varchar not null,
    create_date date not null,
    unique(cognito_id)
);

