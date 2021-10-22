select  count(*) 
from    cloudtrail_consolidated_by_date
where   useridentity.accountid = '123456789012'
and     ingest_date between '2020/10/01' and '2020/10/31'
and     awsregion = 'us-east-1'
