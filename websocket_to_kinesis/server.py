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

""" Sends a minute's worth of timestamp messages to a connected client, 
    then terminates the connection.
    """

import asyncio
from datetime import datetime, timezone
import logging
import os
import time
from websockets.server import serve


logging.basicConfig(level=logging.WARN, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

listen_port = int(os.environ.get("LISTEN_PORT", "8000"))
send_count = int(os.environ.get("SEND_COUNT", "60"))
send_sleep = float(os.environ.get("SEND_SLEEP", "1.0"))


async def main():
    async with serve(send_messages, port=listen_port):
        logger.info(f"server started, listening on port {listen_port}")
        logger.info(f"send count: {send_count}, inter-message sleep: {send_sleep}")
        await asyncio.Future()  # run forever


async def send_messages(websocket):
    logger.info(f"received connection {websocket.id} from {websocket.remote_address}")
    for x in range(send_count):
        await websocket.send(datetime.now(tz=timezone.utc).isoformat())
        time.sleep(send_sleep)
    await websocket.close()


asyncio.run(main())
