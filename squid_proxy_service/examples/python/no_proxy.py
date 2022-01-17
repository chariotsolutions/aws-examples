#!/usr/bin/env python3

""" Retrieves a listing of CloudWatch log groups for the current account/region,
    using a base client configuration. The proxy can be enabled via the 
    HTTP_PROXY and HTTPS_PROXY environment variables.
    """

import boto3
from pprint import pprint

client = boto3.client('sts')

result = client.get_caller_identity()
pprint(result)
