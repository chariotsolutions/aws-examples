-- In this query, the first five predicates are defined as partition fields; the last three are read from data.
-- Since this table uses partition injection, all of the partition predicates must be specified.
-- Partition predicates must use equality tests, so we must explicitly specify all date fields; this will cause us to read three whole months of data to ensure we get the proper range.
--

select  eventname, count(*) 
from    cloudtrail_raw_partition_injection
where   account = '810107213182'
and     region = 'us-east-1'
and     year = '2024'
and     month in ('01', '02', '03')
and     day in ('01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23', '24', '25', '26', '27', '28', '29', '30', '31')
and     eventtime between '2024-02-01T00:00:00Z' and '2024-02-28T23:59:59Z'
and     recipientaccountid = '810107213182'
and     awsregion = 'us-east-1'
group   by 1
order   by 2 desc
limit   10
