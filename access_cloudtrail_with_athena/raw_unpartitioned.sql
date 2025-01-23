-- In this query, all predicates are read from data
--

select  eventname, count(*) 
from    cloudtrail_raw_unpartitioned
where   eventtime between '2024-02-01T00:00:00Z' and '2024-02-28T23:59:59Z'
and     recipientaccountid = '810107213182'
and     awsregion = 'us-east-1'
group   by 1
order   by 2 desc
limit   10
