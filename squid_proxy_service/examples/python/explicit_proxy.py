#!/usr/bin/env python3

""" Retrieves a listing of CloudWatch log groups for the current account/region,
    using an explicit proxy configuration. 
    """

import boto3
import botocore.config
from pprint import pprint


proxies = {
  "http": "http://squid_proxy.internal:3128",
  "https": "http://squid_proxy.internal:3128",
}

boto_config = botocore.config.Config(proxies=proxies)
client = boto3.client('sts', config=boto_config)

result = client.get_caller_identity()
pprint(result)
