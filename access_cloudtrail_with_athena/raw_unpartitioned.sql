select  count(*)
from    cloudtrail_raw_unpartitioned
where   useridentity.accountid = '123456789012'
and     substr(eventtime, 1, 7) = '2020-10'
and     awsregion = 'us-east-1'
