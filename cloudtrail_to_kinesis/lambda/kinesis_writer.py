# Source: https://github.com/kdgregory/aws-misc/blob/trunk/python/kinesis/kinesis_writer.py
################################################################################
# Copyright 2023, Keith D Gregory
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


import boto3
import json
import logging
import re
import time


logger = logging.getLogger("KinesisWriter")
logger.setLevel(logging.DEBUG)


class QueuedMessage:
    """ An internal helper that validates and holds queued messages.
        """

    def __init__(self, message_bytes, partition_key):
        message_length = len(message_bytes)
        partkey_length = len(partition_key.encode())
        record_size = message_length + partkey_length

        if (partkey_length > 256):
            raise ValueError(f"partition key too large: {partkey_length}")
        if (record_size > 1024 * 1024):
            raise ValueError(f"message too large: {record_size} (base message length = {message_length}, partition key length = {partkey_length})")

        self.record_size = record_size
        self.request_form = {
            'Data': message_bytes,
            'PartitionKey': partition_key
        }


class KinesisWriter:

    def __init__(self, client, stream, log_batches=False):
        """ Initializes a new writer.

            client
            stream
            log_batches
            """
        self._client = client
        if stream.startswith("arn:"):
            self._stream_name = re.sub(r".*:", "", stream)
            self._stream_param = { "StreamARN": stream }
        else:
            self._stream_name = stream
            self._stream_param = { "StreamName": stream }
        self._log_batches = log_batches
        self._queue = []
        self._bytes_in_queue = 0
        self.last_batch_size = 0
        self.last_batch_success_count = 0
        self.last_batch_failure_messages = set()

    
    def enqueue(self, message, partition_key=None):
        """ Adds a message to the queue, flushing if configured conditions met.

            message
            partition_key
            """
        if not partition_key:
            partition_key = str(time.time())
        if not isinstance(partition_key, str):
            partition_key = str(partition_key)
        
        if isinstance(message, bytes):
            pass
        elif isinstance(message, str):
            message = message.encode()
        else:
            message = json.dumps(message).encode()

        queued_message = QueuedMessage(message, partition_key)
        if self._enqueue(queued_message):
            self.flush()

    
    def flush(self):
        """ Flushes the queue. 
        
            Returns True if messages remain in queue after flush. To ensure that all
            messages have been sent, you should loop with a short sleep between calls.
            """
        if len(self._queue) == 0:
            return False
        (messages_to_send, messages_to_requeue) = self._split_queue()
        if self._log_batches:
            logger.debug(f"sending {len(messages_to_send)} messages to stream {self._stream_name}")
        response = self._client.put_records(**self._stream_param, Records=[rec.request_form for rec in messages_to_send])
        self._process_results(messages_to_send, messages_to_requeue, response)
        if self._log_batches:
            logger.debug(f"sent {self.last_batch_size} messages to stream {self._stream_name}; {self.last_batch_success_count} successful; errors = {self.last_batch_failure_messages}")
        return len(self._queue) > 0


    def _split_queue(self):
        """ Splits the queue into messages to send (based on count or size) and messages
            to requeue (after any failures). 
            """
        bytes_so_far = 0
        for idx,queued_message in enumerate(self._queue):
            bytes_so_far += queued_message.record_size
            if (idx == 500) or (bytes_so_far >= 5 * 1024 * 1024):
                return (self._queue[:idx], self._queue[idx:])
        return (self._queue, [])


    def _process_results(self, messages_to_send, messages_to_requeue, response):
        """ Rebuilds the queue, including any records that were rejected.
            """
        self._queue = []
        self._bytes_in_queue = 0
        self.last_batch_size = len(messages_to_send)
        self.last_batch_success_count = 0
        self.last_batch_failure_messages = set()
        for idx,record in enumerate(response['Records']):
            if record.get('ErrorCode'):
                self._enqueue(messages_to_send[idx])
                self.last_batch_failure_messages.add(record['ErrorMessage'])
            else:
                self.last_batch_success_count += 1
        for queued_message in messages_to_requeue:
            self._enqueue(queued_message)


    def _enqueue(self, queued_message):
        """ Adds the record to the queue and determines whether the queue should be flushed.
            Called both from initial enqueue() and when processing results.
            """
        self._queue.append(queued_message)
        self._bytes_in_queue += queued_message.record_size
        return (self._bytes_in_queue >= 5 * 1024 * 1024) or (len(self._queue) >= 500)

