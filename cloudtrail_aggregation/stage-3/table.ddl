-- replace MY_BUCKET by your actual bucket name
-- if you decide to change the name of the table, you will also need to change the S3 location and location template

CREATE EXTERNAL TABLE cloudtrail_athena (
        event_id                STRING,
        request_id              STRING,
        event_time              TIMESTAMP,
        event_source            STRING,
        event_name              STRING,
        aws_region              STRING,
        source_ip_address       STRING,
        recipient_account_id    STRING,
        user_identity           STRING,
        invoked_by              STRING,
        principal_id            STRING,
        resources               STRING
)
PARTITIONED BY ( 
        year                    string, 
        month                   string
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe' 
STORED AS PARQUET
LOCATION 's3://MY_BUCKET/cloudtrail_athena/'
TBLPROPERTIES (
    'classification'            = 'parquet',
    'projection.enabled'        = 'true',
    'storage.location.template' = 's3://MY_BUCKET/cloudtrail_athena/${year}/${month}/',
    'projection.year.type'      = 'integer',
    'projection.year.range'     = '2019,2029',
    'projection.year.digits'    = '4',
    'projection.month.type'     = 'integer',
    'projection.month.range'    = '1,12',
    'projection.month.digits'   = '2'
)

