# CloudTrail table definition for Athena

You can [use Athena to query your CloudTrail logs](https://docs.aws.amazon.com/athena/latest/ug/cloudtrail-logs.html),
but it suffers from the "small files" problem. The documentation gives two approaches to partitioning: one using
manual partitions, and one using partition projection.

If your primary use-case is date-based aggregation across accounts and regions, and if your organization account
structure is relatively static, then I think that partition projection is fine. However, if you want to drill into
events for a specific account, region, and date, then patition _injection_ is a better solution.

Here is my version of the AWS table definition, using injection rather than projection:

```
CREATE EXTERNAL TABLE `cloudtrail_raw_injected` (
	`eventversion` string COMMENT 'from deserializer',
	`useridentity` struct < type: string,
	principalid: string,
	arn: string,
	accountid: string,
	invokedby: string,
	accesskeyid: string,
	username: string,
	sessioncontext: struct < attributes: struct < mfaauthenticated: string,
	creationdate: string >,
	sessionissuer: struct < type: string,
	principalid: string,
	arn: string,
	accountid: string,
	username: string >,
	ec2roledelivery: string,
	webidfederationdata: map < string,
	string >> > COMMENT 'from deserializer',
	`eventtime` string COMMENT 'from deserializer',
	`eventsource` string COMMENT 'from deserializer',
	`eventname` string COMMENT 'from deserializer',
	`awsregion` string COMMENT 'from deserializer',
	`sourceipaddress` string COMMENT 'from deserializer',
	`useragent` string COMMENT 'from deserializer',
	`errorcode` string COMMENT 'from deserializer',
	`errormessage` string COMMENT 'from deserializer',
	`requestparameters` string COMMENT 'from deserializer',
	`responseelements` string COMMENT 'from deserializer',
	`additionaleventdata` string COMMENT 'from deserializer',
	`requestid` string COMMENT 'from deserializer',
	`eventid` string COMMENT 'from deserializer',
	`resources` array < struct < arn: string,
	accountid: string,
	type: string >> COMMENT 'from deserializer',
	`eventtype` string COMMENT 'from deserializer',
	`apiversion` string COMMENT 'from deserializer',
	`readonly` string COMMENT 'from deserializer',
	`recipientaccountid` string COMMENT 'from deserializer',
	`serviceeventdetails` string COMMENT 'from deserializer',
	`sharedeventid` string COMMENT 'from deserializer',
	`vpcendpointid` string COMMENT 'from deserializer',
	`tlsdetails` struct < tlsversion: string,
	ciphersuite: string,
	clientprovidedhostheader: string > COMMENT 'from deserializer'
)
PARTITIONED BY (
	`account` string,
	`region` string,
	`year` string,
	`month` string,
	`day` string
)
ROW FORMAT SERDE 'org.apache.hive.hcatalog.data.JsonSerDe'
STORED AS INPUTFORMAT 'com.amazon.emr.cloudtrail.CloudTrailInputFormat' OUTPUTFORMAT 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
LOCATION 's3://YOUR_BUCKET/'
TBLPROPERTIES (
	'classification' = 'cloudtrail',
	'projection.enabled' = 'true',
	'projection.account.type' = 'injected',
	'projection.region.type' = 'injected',
	'projection.year.type' = 'injected',
	'projection.month.type' = 'injected',
	'projection.day.type' = 'injected',
	'storage.location.template' = 's3://YOUR_BUCKET/AWSLogs/YOUR_ORG_ID/${account}/CloudTrail/${region}/${year}/${month}/${day}/'
)
```

Replace `YOUR_BUCKET` and `YOUR_ORG_ID`, and paste the query into the Athena query editor. You can get these values by
opening the trail in the CloudTail Console and looking for "Trail log location" (this will also include the current
account number, which you don't care about).

To query the table, you must specify a value for each of the partitioning columns. For example, to see the failed requests for
a specific account/region/date:

```
select  eventtime, eventid, eventname, errorcode, errormessage
from    "default"."cloudtrail_raw_injected"
where   account = '123456789012'
and     region = 'us-east-1'
and     year = '2025'
and     month = '01'
and     day = '22'
and     errorcode is not null
order   by eventtime desc
```
