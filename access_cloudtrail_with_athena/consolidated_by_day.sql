-- In this query, the first predicate uses a partition field; the last three are read from data.
-- Because CloudTrail events may be written in files that cross date boundaries, our date partition predicate includes an extra day on either side.
--

select  eventname, count(*) 
from    cloudtrail_raw_partition_projection
where   ingest_date between '2024/01/31' and '2024/03/01'
and     eventtime between '2024-02-01T00:00:00Z' and '2024-02-28T23:59:59Z'
and     recipientaccountid = '810107213182'
and     awsregion = 'us-east-1'
group   by 1
order   by 2 desc
limit   10
