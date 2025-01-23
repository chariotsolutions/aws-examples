CREATE EXTERNAL TABLE `cloudtrail_raw_partition_projection` (
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
  `account_id` string, 
  `region` string, 
  `ingest_date` string)
ROW FORMAT SERDE 
  'org.apache.hive.hcatalog.data.JsonSerDe' 
STORED AS INPUTFORMAT 
  'com.amazon.emr.cloudtrail.CloudTrailInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
LOCATION
  's3://com-chariotsolutions-cloudtrail/'
TBLPROPERTIES (
  'projection.account_id.type'='enum', 
  'projection.account_id.values'='045205798610,067549028710,163319550195,219289705433,332284445751,362296207274,366425516243,403077131242,440345792023,541319400331,555270592756,567196586496,748558724567,751064731489,780250676544,810107213182,897893808641', 
  'projection.enabled'='true', 
  'projection.ingest_date.format'='yyyy/MM/dd', 
  'projection.ingest_date.range'='2019/10/01,NOW', 
  'projection.ingest_date.type'='date', 
  'projection.region.type'='enum', 
  'projection.region.values'='ap-northeast-1,ap-northeast-2,ap-northeast-3,ap-south-1,ap-southeast-1,ap-southeast-2,ca-central-1,eu-central-1,eu-north-1,eu-west-1,eu-west-2,eu-west-3,sa-east-1,us-east-1,us-east-2,us-west-1,us-west-2', 
  'storage.location.template'='s3://com-chariotsolutions-cloudtrail/AWSLogs/o-x72e8b2quf/${account_id}/CloudTrail/${region}/${ingest_date}'
)
