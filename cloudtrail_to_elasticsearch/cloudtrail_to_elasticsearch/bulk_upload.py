#!/usr/bin/env python3
################################################################################
# Copyright Chariot Solutions
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

""" Bulk-loads events: reads files from either S3 or the local filesystem,
    batches them as possible, and writes to Elasticsearch.

    Intended to be invoked from the command-line, using one of these forms:

        python -m cloudtrail_to_elasticsearch.bulk_upload [--dates START_DATE END_DATE] --s3 BUCKET_NAME [PREFIX]
        python -m cloudtrail_to_elasticsearch.bulk_upload [--dates START_DATE END_DATE] --local FILE_OR_DIRECTORY

    Must have the following environment variables set:
"""

import argparse
import os
import pathlib
import re
import sys

from cloudtrail_to_elasticsearch import processor
from cloudtrail_to_elasticsearch.s3_helper import S3Helper


##
## Environment variables - dereference here to fail fast
##

ES_HOSTNAME = os.environ['ES_HOSTNAME']


##
## Invocation arguments
##

arg_parser = argparse.ArgumentParser(description="Bulk-uploads CloudTrail events to Elasticsearch")

arg_parser.add_argument("--dates",
                        nargs=2,
                        metavar="START_DATE END_DATE",
                        dest='date_range',
                        help="""Starting and ending rate range for selected files, in form
                                YYYY-MM-DD. These are matched against the date embedded in
                                the filename. To select an unbounded range, use 0000-01-01
                                for the low end, 9999-12-31 for the high end.
                                """)

arg_parser.add_argument("--local",
                        metavar="FILE_OR_DIRECTORY",
                        dest='local_path',
                        help="""A single file or directory of files to be uploaded.
                                """)
arg_parser.add_argument("--s3",
                        nargs="+",
                        metavar=("BUCKET", "PREFIX"),
                        dest='s3_config',
                        help="""Destination on S3 where CloudTrail files are located, with optional prefix.
                                Can restrict the files that are processed by providing start and end dates,
                                formatted "YYYY-MM-DD"; use dummy values (eg, "9999-12-31") to bound on one
                                side only.
                                """)
args = arg_parser.parse_args()

args.date_range = args.date_range or ("0000-01-01", "9999-12-31")
args.date_start = args.date_range[0].replace("-", "")
args.date_finish = args.date_range[1].replace("-", "")


##
## Helper functions
##

FILENAME_REGEX = re.compile(r".*_CloudTrail_[^_]*_(\d{8})T\d{4}Z_.*json.gz")

def include_file(filename):
    """ Verifies that the passed filename matches a CloudTrail upload file, and
        that it's between the configured dates.
        """
    m = FILENAME_REGEX.match(filename)
    return m and m.group(1) >= args.date_start and m.group(1) <= args.date_finish


def local_files(root):
    """ Retrieves a list of files from the local filesystem that match the
        specified date range.
        """
    def recursive_select(path, acc):
        if path.is_file():
            filename = str(path)
            if include_file(filename):
                acc.append(filename)
        else:
            for child in pathlib.Path(path).iterdir():
                recursive_select(child, acc)
    result = []
    recursive_select(pathlib.Path(root), result)
    return result


def s3_files(s3_helper, bucket, prefix):
    """ Retrieves a list of files from S3 that match the provided date range.
        """
    file_list = []
    def select_files(b,k):
        if include_file(k):
            file_list.append(k)
    s3_helper.iterate_bucket(bucket, prefix, select_files)
    return file_list


##
## The main event
##

s3 = S3Helper()
px = processor.create()

if args.local_path:
    for filename in local_files(args.local_path):
        print(f"processing local file: {filename}")
        px.process_local_file(filename, flush=False)
    px.flush()
elif args.s3_config:
    bucket = args.s3_config[0]
    prefix = args.s3_config[1] if len(args.s3_config) > 1 else ""
    for key in s3_files(s3, bucket, prefix):
        print(f"processing S3 file: s3://{bucket}/{key}")
        px.process_from_s3(bucket, key, flush=False)
    px.flush()
else:
    print("", file=sys.stderr)
    arg_parser.print_help()
