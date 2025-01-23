CREATE EXTERNAL TABLE `cloudtrail_single_file` (
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
ROW FORMAT SERDE 
  'org.apache.hive.hcatalog.data.JsonSerDe' 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.mapred.TextInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
LOCATION
  's3://BUCKET/PREFIX/'
