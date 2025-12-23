--
-- Redshift table to hold CloudTrail events.
--
--##############################################################################
--
-- MIT No Attribution
--
-- Copyright Chariot Solutions
--
-- Permission is hereby granted, free of charge, to any person obtaining a copy of this
-- software and associated documentation files (the "Software"), to deal in the Software
-- without restriction, including without limitation the rights to use, copy, modify,
-- merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
-- permit persons to whom the Software is furnished to do so.
-- 
-- THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
-- INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
-- PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
-- HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
-- OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
-- SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
--
--##############################################################################

CREATE TABLE cloudtrail_events
(
        event_id                        varchar(64)         ENCODE RAW,
        event_time                      timestamp,
        event_name                      varchar(64)         ENCODE TEXT255,
        event_category                  varchar(64)         ENCODE TEXT255,
        event_type                      varchar(64)         ENCODE TEXT255,
        event_version                   varchar(64)         ENCODE TEXT255,
        aws_region                      varchar(64)         ENCODE TEXT255,
        event_source                    varchar(64)         ENCODE TEXT255,
        management_event                boolean,
        read_only                       boolean,
        api_version                     varchar(64)         ENCODE TEXT255,
        recipient_account_id            varchar(64)         ENCODE TEXT255,
        source_ip_address               varchar(64)         ENCODE RAW,
        request_id                      varchar(255)        ENCODE RAW,
        shared_event_id                 varchar(64)         ENCODE RAW,
        request_parameters              varchar(65535),
        response_elements               varchar(65535),
        resources                       varchar(65535),
        additional_event_data           varchar(65535),
        service_event_details           varchar(65535),
        user_agent                      varchar(65535),
        user_identity                   varchar(65535),
        tls_details                     varchar(65535),
        vpc_endpoint_id                 varchar(64)         ENCODE TEXT255,
        vpc_endpoint_account_id         varchar(64)         ENCODE TEXT255,
        error_code                      varchar(255)        ENCODE TEXT255,
        error_message                   varchar(65535)
)
DISTSTYLE   EVEN
SORTKEY     ( event_time );
