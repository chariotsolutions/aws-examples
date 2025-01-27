#!/usr/bin/env python
################################################################################
#
# MIT No Attribution
#
# Copyright Chariot Solutions
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
################################################################################

""" Connects to a web-socket specified via environment variable, reads all of its
    messages, and sends them to a Kinesis stream specified via another envar.
    """

import boto3
import os
import logging
import random
import time
import websockets.sync.client as ws_client


logging.basicConfig(level=logging.WARN, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def main(kinesis_client, server_url, stream_name):
    while True:
        try:
            with ws_client.connect(server_url) as websocket:
                logger.info(f"opened connection {websocket.id} to {websocket.remote_address}")
                for msg in websocket:
                    logger.debug(msg)
                    kinesis_client.put_record(StreamName=stream_name, PartitionKey=str(random.random()), Data=msg.encode('utf-8'))
                logger.info("connection closed by server")
        except:
            logger.warning("exception while processing", exc_info=True)
            time.sleep(30)


if __name__ == "__main__":
    kinesis_client = boto3.client('kinesis')
    server_url = os.environ['SERVER_URL']
    stream_name = os.environ['STREAM_NAME']
    main(kinesis_client, server_url, stream_name)
