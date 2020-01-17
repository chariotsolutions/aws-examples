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
import os
import re
import sys

import es_helper
import s3_helper


class Processor:
    """ Functions to extract, transform, and upload a single file's events.
        This is invoked either from the Lambda or bulk_upload.py; it is not
        normally invoked independently.
    """

    def __init__(self, es_helper, s3_helper):
        self.es_helper = es_helper
        self.s3_helper = s3_helper

    def process_from_s3(self, bucket, key):
        index = index_name(key)
        if index:
            print(f'processing s3://{bucket}/{key}')
            content = self.s3_helper.retrieve(bucket, key)
            self.process(content, index)
        else:
            print(f'cannot extract index name from key: {key}')

    def process(self, content, index):
        parsed = json.loads(content)
        transformed = transform_events(parsed.get('Records', []))
        self.es_helper.upload(transformed, index)


## the following are exposed to simplify testing ... plus, there's no good
## reason to wrap them in an object: they're simple imperative functions,
## without collaborators

FILENAME_REGEX = re.compile(r'.*CloudTrail/[^/]+/(\d{4})/(\d{2})/\d{2}/.*')

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
        if isinstance(v, set):
            tmp = v
            v = list()
            for item in tmp:
                v.append(str(item))
        dst[k] = v
    return dst

