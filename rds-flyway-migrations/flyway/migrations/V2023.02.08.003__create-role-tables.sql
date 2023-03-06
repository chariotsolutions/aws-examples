CREATE TABLE IF NOT EXISTS app_roles (
    role_id uuid primary key default gen_random_uuid(),
    role_name varchar not null
);

CREATE TABLE IF NOT EXISTS user_app_roles (
    user_id uuid references user_accounts,
    role_id uuid references app_roles,
    active boolean not null default true,
    primary key (user_id, role_id)
);

insert into app_roles(role_name) values ('admin');
insert into app_roles(role_name) values ('user');

select * from app_roles;

