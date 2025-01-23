select  eventtime, eventid, eventname, errorcode, errormessage
from    "default"."cloudtrail_raw_injected"
where   account = '123456789012'
and     region = 'us-east-1'
and     year = '2025'
and     month = '01'
and     day = '22'
and     errorcode is not null
order   by eventtime desc
