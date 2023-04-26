################################################################################
# Copyright 2019 Chariot Solutions
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
################################################################################


import json
import requests
import os

from aws_requests_auth.aws_auth import AWSRequestsAuth

DEFAULT_BATCH_SIZE = 7680 * 1024


class ESHelper:

    """ An instance of this class aggregates events into batche updates to a single
        index, ensuring that the index exists.

        To use, call add_events() as many times as needed, followed by flush(). The
        former will accumulate events into a batch, automatically calling flush if
        the the configured batch size is exceeded or the caller starts writing to a
        new index.

        By default, instances are configured to access an AWS managed Elasticsearch
        cluster, retrieving the hostname and AWS credentials from the environment.

        For testing, you can construct an instance with explicit hostname, optional
        AWS authorization credentials, and an HTTP endpoint. You can also create a
        mock instance.
    """

    def __init__(self, hostname=None, use_aws_auth=True, use_https=True, index_config=None, batch_size=DEFAULT_BATCH_SIZE):
        """
            hostname      If provided, the hostname of the Elasticsearch cluster. If not
                          provided, this is read from the environment variable ES_HOSTNAME.
            use_aws_auth  If true, uses AWS signed requests; if false, simple HTTP(S).
            use_https     If true, uses HTTPS requests; if false, HTTP.
            index_config  If provided, used to create a new index. This is a Python object
                          that corresponds to the Elasticsearch configuration JSON.
            batch_size    if provided, defines a trigger for writing batches to Elasticsearch.
                          AWS Opensearch has been observed to reject requests > 1 MB, even
                          though the Elasticsearch docs say that it will accept up to 100 MB.
        """
        if hostname:
            self.hostname = hostname
        else:
            self.hostname = os.environ['ES_HOSTNAME']
        if use_aws_auth:
            auth_args = {}
            auth_args['aws_access_key']         = os.environ['AWS_ACCESS_KEY_ID']
            auth_args['aws_secret_access_key']  = os.environ['AWS_SECRET_ACCESS_KEY']
            auth_args['aws_region']             = os.environ['AWS_REGION']
            auth_args['aws_service']            = 'es'
            auth_args['aws_host']               = self.hostname
            if os.environ.get('AWS_SESSION_TOKEN'):
                auth_args['aws_token']          = os.environ.get('AWS_SESSION_TOKEN')
            self.auth = AWSRequestsAuth(**auth_args)
        else:
            self.auth = None
        if use_https:
            self.protocol = "https"
        else:
            self.protocol = "http"
        self.index_config = index_config
        self.max_batch_size = batch_size
        self.current_index = None
        self.current_batch = []
        self.current_batch_size = 0


    def add_events(self, events, index):
        """ Adds events to the batch for the specified index. If this causes the
            batch to exceed batch-size, or is for a different index than previous
            calls, it will invoke flush().
        """
        if self.current_index != index:
            self.flush()  # this is a no-op first time through
            self.current_index = index
        for event in events:
            prepared = self.prepare_event(event, self.current_index)
            self.current_batch.append(prepared)
            self.current_batch_size += len(prepared)
            if self.current_batch_size > self.max_batch_size:
                self.flush()


    def prepare_event(self, event, index):
        return "\n".join([
            json.dumps({ "index": { "_index": index, "_id": event['eventID'] }}),
            json.dumps(event)
            ]) + "\n"


    def flush(self):
        """ Writes all events in the current batch to Elasticsearch, then clears
            the batch.
            """
        # no-op to simplify calling code
        if not self.current_index or not self.current_batch:
            return
        self.ensure_index_exists(self.current_index)
        print(f'writing {len(self.current_batch)} events to index {self.current_index}')
        rsp = self.do_request(requests.post, "_bulk", "".join(self.current_batch), 'application/x-ndjson')
        if rsp.status_code == 200:
            # individual records may be rejected -- we'll assume them damaged and drop
            self.log_record_errors(rsp)
            self.current_batch = []
            self.current_batch_size = 0
        elif rsp.status_code == 429:
            print(f'upload throttled; retrying')
            # we'll hope that it succeeds before we blow stack
            self.flush()
        else:
            # log the error, leave the events in queue for future attempt
            print(f'upload failed: status {rsp.status_code}, description = {rsp.text}')


    def ensure_index_exists(self, index):
        """ Called before uploading a series of events, to verify that the index
            exists, and to create it if not. This allows us to configure the index
            appropriately for CloudTrail events.
        """
        rsp = self.do_request(requests.get, index)
        if rsp.status_code == 200:
            return
        elif rsp.status_code == 404:
            if self.index_config:    
                print(f"creating index: {index}")
                rsp = self.do_request(requests.put, index, self.index_config)
                if rsp.status_code != 200:
                    raise Exception(f'failed to create index: {rsp.text}')
            else:
              pass  # first PUT will create index
        else:
            print(f'failed to retrieve index status: {rsp.text}')


    def do_request(self, fn, path, body=None, content_type='application/json'):
        url = self.protocol + "://" + self.hostname + "/" + path
        kwargs = {}
        if body:
            kwargs['data'] = body
            kwargs['headers'] = {'Content-Type': content_type}
        if self.auth:
            kwargs['auth'] = self.auth
        rsp = fn(url, **kwargs)
        return rsp


    def log_record_errors(self, rsp):
        result = json.loads(rsp.text)
        if not result.get('errors'):
            print("no errors")
            return
        failed_records = set()
        for item in result.get('items', []):
            item = item.get('index', {})
            if item.get('status', 500) > 299:
                failed_records.add(item.get('_id'))
        print(f'upload failed for {len(failed_records)} records: {list(failed_records)[:5]}')
