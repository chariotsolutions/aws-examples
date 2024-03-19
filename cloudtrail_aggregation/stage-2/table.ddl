CREATE EXTERNAL TABLE cloudtrail_monthly (
    event_id                string, 
    request_id              string, 
    shared_event_id         string, 
    event_time              timestamp, 
    event_name              string, 
    event_source            string, 
    event_version           string, 
    aws_region              string, 
    source_ip_address       string, 
    recipient_account_id    string, 
    user_identity           string, 
    request_parameters      string, 
    response_elements       string, 
    additional_event_data   string, 
    resources               string
)
PARTITIONED BY ( 
    year                    string, 
    month                   string
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe' 
STORED AS 
    INPUTFORMAT 'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat' 
    OUTPUTFORMAT 'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat'
LOCATION 's3://MY_BUCKET/cloudtrail_monthly/'
TBLPROPERTIES (
    'classification'            = 'parquet',
    'projection.enabled'        = 'true',
    'storage.location.template' = 's3://MY_BUCKET/cloudtrail_monthly/${year}/${month}/',
    'projection.year.type'      = 'integer',
    'projection.year.range'     = '2019,2029',
    'projection.year.digits'    = '4',
    'projection.month.type'     = 'integer',
    'projection.month.range'    = '1,12',
    'projection.month.digits'   = '2'
)
