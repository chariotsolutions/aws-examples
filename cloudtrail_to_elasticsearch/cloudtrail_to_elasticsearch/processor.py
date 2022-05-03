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

""" This is the main logic module. It relies on external classes to read files
    from S3 and write events to Elasticsearch.
    """


import gzip
import json
import os
import re
import sys

from cloudtrail_to_elasticsearch.es_helper import ESHelper
from cloudtrail_to_elasticsearch.s3_helper import S3Helper


# the index configuration that we'll use

DEFAULT_INDEX_CONFIG = json.dumps({
    'settings': {
        'index.mapping.total_fields.limit': 8192,
        'index.number_of_shards': 1,
        'index.number_of_replicas': 0
    },
    'mappings': {
        'dynamic_templates': [
            {
                'flattened_requestParameters': {
                        'path_match': 'requestParameters_flattened.*',
                        'mapping': { 'type': 'text' }
                }
            }, {
                'flattened_responseElements': {
                        'path_match': 'responseElements_flattened.*',
                        'mapping': { 'type': 'text' }
                }
            }, {
                'flattened_resources': {
                        'path_match': 'resources_flattened.*',
                        'mapping': { 'type': 'text' }
                }
            }
        ],
        'properties': {
            'apiVersion': { 'type': 'text' }
        }
    }
})


def create():
  """ Factory method to create a default instance.
  """
  return Processor(ESHelper(index_config=DEFAULT_INDEX_CONFIG),
                   S3Helper())


class Processor:
    """ Functions to extract, transform, and upload a single file's events.
        This is invoked either from the Lambda or bulk_upload.py; it is not
        normally invoked independently.
    """

    def __init__(self, es_helper, s3_helper):
        self.es_helper = es_helper
        self.s3_helper = s3_helper


    def process_local_file(self, pathname, flush=True):
        index = index_name(pathname)
        if index:
            with open (pathname, mode='rb') as f:
                data = f.read()
            if data.startswith(b'\x1f\x8b'):
                 data = gzip.decompress(data)
            self.process(str(data, 'utf-8'), index, flush)
        else:
            print(f'cannot extract index name from key: {key}')


    def process_from_s3(self, bucket, key, flush=True):
        index = index_name(key)
        if index:
            content = self.s3_helper.retrieve(bucket, key)
            self.process(content, index, flush)
        else:
            print(f'cannot extract index name from key: {key}')


    def process(self, content, index, flush=True):
        parsed = json.loads(content)
        transformed = transform_events(parsed.get('Records', []))
        self.es_helper.add_events(transformed, index)
        if flush:
            self.flush()


    def flush(self):
        self.es_helper.flush()


## the following are exposed to simplify testing ... plus, there's no good
## reason to wrap them in an object: they're simple imperative functions,
## without collaborators

FILENAME_REGEX = re.compile(r'.*_(\d{4})(\d{2})\d{2}T\d{4}Z_\w+.json.gz')

def index_name(key):
    match = FILENAME_REGEX.match(key)
    if match:
        return f'cloudtrail-{match.group(1)}-{match.group(2)}'
    else:
        return None


def transform_events(events):
    for event in events:
        flatten(event, 'requestParameters')
        flatten(event, 'responseElements')
        flatten(event, 'resources')
    return events


def flatten(event, key):
    src = event.pop(key, None);
    if not src:
        return
    if isinstance(src, dict):
        dst = flatten_dict(src, {})
    elif isinstance(src, list):
        dst = flatten_list(key, src, {})
    else:
        # this is something that doesn't need to be flattened; put it back
        event[key] = src
        return
    event[key + "_raw"] = json.dumps(src)
    event[key + "_flattened"] = transform_flattened_elements(dst)


def flatten_dict(src, dst):
    for key in src.keys():
        # CloudTrail events sometimes contains blank keys; we'll skip those
        if key:
            flatten_item(key, src[key], dst)
    return dst


def flatten_list(key, val, dst):
    for item in val:
        flatten_item(key, item, dst)
    return dst


def flatten_item(key, val, dst):
    if isinstance(val, dict):
        flatten_dict(val, dst)
    elif isinstance(val, list):
        flatten_list(key, val, dst)
    else:
        if not key in dst:
            dst[key] = set()
        dst[key].add(val)
    return dst


def transform_flattened_elements(src):
    dst = {}
    for (k, v) in src.items():
        # Elasticsearch doesn't like keys that have dots in them
        k = k.replace(".", "_")
        # json.dumps() doesn't like sets
        if isinstance(v, set):
            tmp = v
            v = list()
            for item in tmp:
                v.append(str(item))
        dst[k] = v
    return dst

