-- replace MY_BUCKET by your actual bucket name
-- replace MONTH and YEAR by the actual month and year that you want to transform
-- remember to drop this table once you've verified the transformed data

CREATE TABLE cloudtrail_athena_temp_YEAR_MONTH
WITH (
        format = 'parquet',
        bucketed_by = ARRAY['event_id'], 
        bucket_count = 4,
        external_location = 's3://MY_BUCKET/cloudtrail_athena/YEAR/MONTH
        write_compression = 'SNAPPY'
) AS
select  eventid                                                 as event_id,
        requestid                                               as request_id,
        cast(from_iso8601_timestamp(eventtime) as timestamp)    as event_time,
        eventsource                                             as event_source,
        eventname                                               as event_name,
        awsregion                                               as aws_region,
        sourceipaddress                                         as source_ip_address,
        recipientaccountid                                      as recipient_account_id,
        json_format(cast (useridentity as JSON))                as user_identity,
        useridentity.invokedby                                  as invoked_by,
        useridentity.principalid                                as principal_id,
        json_format(cast (resources as JSON))                   as resources
from    default.cloudtrail_daily
where   year = 'YEAR'
and     month = 'MONTH


