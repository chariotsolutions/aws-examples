select  count(*)
from    cloudtrail_raw_partitioned
where   account_id = '123456789012'
and     ingest_date between '2020/10/01' and '2020/10/31'
and     region = 'us-east-1'
