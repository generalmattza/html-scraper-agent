#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Created By  : Matthew Davidson
# Created Date: 2023-01-23
# version ='1.0'
# ---------------------------------------------------------------------------
"""a_short_module_description"""
# ---------------------------------------------------------------------------

import asyncio
from typing import Union
from collections import deque
from buffered.buffer import Buffer


class HTMLScraperAgent:

    def __init__(
        self, buffer: Union[list, deque, Buffer], server_address: tuple = None
    ):
        self._buffer = buffer
        self.server_address = server_address or ("localhost", 0)

    async def do_work_periodically(self, update_interval=None):
        update_interval = update_interval or self.update_interval
        while True:
            await self.do_work()
            await asyncio.sleep(update_interval)

    async def do_work(self, message="", server_address=None):
        server_address = server_address or self.server_address

        # Get do data
        # data = do_something(server_address)

        # Add to input buffer
        # try:
        #   # If Buffer type, use put method to ensure dequeue is used from correct side
        #     self._buffer.put(data)
        # except AttributeError:
        #     self._buffer.append(data)
