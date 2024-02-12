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

def load_config(filepath: Union[str, Path]) -> dict:
    if isinstance(filepath, str):
        filepath = Path(filepath)

    if not Path(filepath).exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    # if extension is .json
    if filepath.suffix == ".json":
        import json

        with open(filepath, "r") as file:
            return json.load(file)

    # if extension is .yaml
    if filepath.suffix == ".yaml":
        import yaml

        with open(filepath, "r") as file:
            return yaml.safe_load(file)
    # if extension is .toml
    if filepath.suffix == ".toml":
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib

        with open(filepath, "rb") as file:
            return tomllib.load(file)

    # else load as binary
    with open(filepath, "rb") as file:
        return file.read()

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
