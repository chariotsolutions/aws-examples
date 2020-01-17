#!/usr/bin/env python3
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


TOTAL_FIELDS_LIMIT = 4096

class ESHelper:

    """ Encapsulates operations against an Elasticsearch cluster.

        By default, instances are configured to access an AWS managed Elasticsearch
        cluster, retrieving the hostname and AWS credentials from the environment.

        For testing, you can construct an instance with explicit hostname, optional
        AWS authorization credentials, and an HTTP endpoint. You can also create a
        mock instance.
    """

    def __init__(self, hostname=None, use_aws_auth=True, use_https=True):
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
    

    def upload(self, events, index):
        """ Uploads a batch of events to the specified index, creating it if necessary.
        """
        print(f'writing {len(events)} events to index {index}')
        self.ensure_index_exists(index)
        updates = [self.prepare_event(event, index) for event in events]
        rsp = self.do_request(requests.post, "_bulk", "".join(updates), 'application/x-ndjson')
        self.log_upload_errors(rsp)
        

    def ensure_index_exists(self, index):
        """ Called before uploading a series of events, to verify that the index
            exists, and to create it if not. This allows us to configure the index
            appropriately for CloudTrail events.
        """
        rsp = self.do_request(requests.get, index)
        if rsp.status_code == 200:
            return
        elif rsp.status_code == 404:
            print("creating index")
            settings = json.dumps({
                "settings": {
                    "index.mapping.total_fields.limit": TOTAL_FIELDS_LIMIT
                }
            })
            rsp = self.do_request(requests.put, index, settings)
            if rsp.status_code != 200:
                print(f'failed to create index: {rsp.text}')
        else:
            print(f'failed to retrieve index status: {rsp.text}')


    def prepare_event(self, event, index):
        return "\n".join([
            json.dumps({ "index": { "_index": index, "_type": "cloudtrail-event", "_id": event['eventID'] }}),
            json.dumps(event)
            ]) + "\n"

    
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
    
    
    def log_upload_errors(self, rsp):
        if rsp.status_code != 200:
            print(f'upload failed: status {rsp.status_code}, description = {rsp.text}')
            return
        result = json.loads(rsp.text)
        if not result.get('errors'):
            print("no errors")
            return
        messages = set()
        failed_records = set()
        for item in result.get('items', []):
            item = item.get('index', {})
            if item.get('status', 500) > 299:
                messages.add(item.get('error', {}).get('reason'))
                failed_records.add(item.get('_id'))
        print(f'upload failed for {len(failed_records)} records:\n{messages}')
            
