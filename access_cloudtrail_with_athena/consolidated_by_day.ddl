--
-- NOTE: This table uses the OpenX JSON SerDe rather than the Hive SerDe. The latter has
--       consistent issues with parsing the "requestparameters" and "responseelements"
--       fields, resulting in silent data loss.
--

CREATE EXTERNAL TABLE `cloudtrail_consolidated_by_date` (
    eventversion STRING,
    useridentity STRUCT<
                   type:STRING,
                   principalid:STRING,
                   arn:STRING,
                   accountid:STRING,
                   invokedby:STRING,
                   accesskeyid:STRING,
                   username:STRING,
                   onbehalfof: STRUCT<
                        userid: STRING,
                        identitystorearn: STRING>,
      sessioncontext:STRUCT<
        attributes:STRUCT<
                   mfaauthenticated:STRING,
                   creationdate:STRING>,
        sessionissuer:STRUCT<  
                   type:STRING,
                   principalid:STRING,
                   arn:STRING, 
                   accountid:STRING,
                   username:STRING>,
        ec2roledelivery:string,
        webidfederationdata: STRUCT<
                   federatedprovider: STRING,
                   attributes: map<string,string>>
      >
    >,
    eventtime STRING,
    eventsource STRING,
    eventname STRING,
    awsregion STRING,
    sourceipaddress STRING,
    useragent STRING,
    errorcode STRING,
    errormessage STRING,
    requestparameters STRING,
    responseelements STRING,
    additionaleventdata STRING,
    requestid STRING,
    eventid STRING,
    resources ARRAY<STRUCT<
                   arn:STRING,
                   accountid:STRING,
                   type:STRING>>,
    eventtype STRING,
    apiversion STRING,
    readonly STRING,
    recipientaccountid STRING,
    serviceeventdetails STRING,
    sharedeventid STRING,
    vpcendpointid STRING,
    vpcendpointaccountid STRING,
    eventcategory STRING,
    addendum STRUCT<
      reason:STRING,
      updatedfields:STRING,
      originalrequestid:STRING,
      originaleventid:STRING>,
    sessioncredentialfromconsole STRING,
    edgedevicedetails STRING,
    tlsdetails STRUCT<
      tlsversion:STRING,
      ciphersuite:STRING,
      clientprovidedhostheader:STRING>
)
PARTITIONED BY ( 
  `ingest_date` string)
ROW FORMAT SERDE 
  'org.openx.data.jsonserde.JsonSerDe' 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.mapred.TextInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
LOCATION
  's3://com-chariotsolutions-kgregory-data/cloudtrail_daily/'
TBLPROPERTIES (
  'projection.enabled'='true', 
  'projection.ingest_date.format'='yyyy/MM/dd', 
  'projection.ingest_date.range'='2024/01/01,NOW', 
  'projection.ingest_date.type'='date', 
  'storage.location.template'='s3://com-chariotsolutions-kgregory-data/cloudtrail_daily/${ingest_date}/'
)
