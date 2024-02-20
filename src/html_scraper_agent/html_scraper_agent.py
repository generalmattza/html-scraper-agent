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
from bs4 import BeautifulSoup
import requests
import re
from fast_database_clients.fast_influxdb_client.influx_metric import InfluxMetric
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

SCRAPER_FILEPATH = "./config/webscraper.yaml"
MEASUREMENT_FILEPATH = "./config/measurements.yaml"
HTML_FILEPATH = "./config/test.html"
MEASUREMENT = "liner_heater"


class GetRequestUnsuccessful(Exception):
    pass


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

        self._timestamp_template = load_config(SCRAPER_FILEPATH)
        self._id_list = []
        self._timestamp_list = []
        for timestamp, ids in self._timestamp_template.items():
            if timestamp != "no_timestamp":
                self._timestamp_list.append(timestamp)
            for id in ids:
                self._id_list.append(id)

    def fetch_html_content(self, url):

        # Construct the URL with the given IP address and optional path
        try:
            # Make a GET request to the URL
            response = requests.get(url)
        except requests.exceptions.ConnectionError as e:
            # logger.warning("HTML GET request was unsuccessful", extra=dict(details=e))
            # raise GetRequestUnsuccessful
            pass

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Return the HTML content if successful
            return response.text
        else:
            # Print an error message if the request fails and return None
            # logger.warning(f"Failed to retrieve HTML. Status code: {response.status_code}")
            raise GetRequestUnsuccessful

    def remove_null_values_from_dict(self, result_dict, null=("nan", "", None)):

        assert isinstance(result_dict, dict)
        assert isinstance(null, (str, tuple, list))
        # if null is singular, then make it into a tuple
        if not isinstance(null, (list, tuple)):
            null = null
        result_dict_copy = result_dict.copy()
        for k, v in result_dict.items():
            if v in null:
                result_dict_copy.pop(k)
        return result_dict_copy

    def extract_elements_by_ids(self, html, id_list):

        result_dict = {}

        if isinstance(html, str):
            soup = BeautifulSoup(html, "html.parser")
        else:
            soup = html

        # Ensure id_list is a list, even if it contains a single ID
        if not isinstance(id_list, list):
            id_list = [id_list]

        for element_id in id_list:
            element = soup.find(id=element_id)

            if element:
                result_dict[element_id] = element.text

        result_dict = self.remove_null_values_from_dict(result_dict)

        return result_dict

    def scrape_data(self, server_address) -> dict:

        try:
            # Fetch HTML content from the specified address and path
            html = self.fetch_html_content(server_address)
        except Exception:
            # GetRequestUnsuccessful:  # CHECK EXCEPTION TYPE WHEN NOT CONNECTED
            # If unsuccessful, then restart loop and try again
            logger.warning("Fetch unsuccessful")
            return

            # Reading html text file instead
            # with open(HTML_FILEPATH) as file:
            #    html = file.read()
        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")

        # Scrape data from the parsed HTML
        data = self.extract_elements_by_ids(soup, self._id_list)
        timestamps = self.extract_elements_by_ids(soup, self._timestamp_list)

        return data, timestamps

    def convert_to_float(self, string):

        # Use regular expression to remove non-numeric characters
        numeric_string = re.sub(r"[^0-9.]+", "", string)
        result_float = float(numeric_string)

        return result_float

    def convert_values(self, value, value_type):

        if value_type == "float":
            return self.convert_to_float(value)
        elif value_type == "string":
            return str(value)
        else:
            # Handle other categories as needed
            return value

    def scrape_to_metric(self, server_address) -> list:

        try:
            scraped_data, scraped_timestamps = self.scrape_data(server_address)
        except TypeError:
            return
        metric_list = []
        target_ids = load_config(MEASUREMENT_FILEPATH)

        for key, value in scraped_data.items():
            # Scraped id exists within target_id to upload to DB
            if key in target_ids.keys():

                # Check the time from target_id to grab the correct time
                for timestamp_id, id_list in self._timestamp_template.items():
                    if key in id_list:
                        date_fmt = "%Y-%m-%d %H:%M:%S"
                        # NOTE: Could improve this section to account if for some reason timestamp
                        #       does not exist -> t = datetime.now()
                        if timestamp_id == "no_timestamp":
                            t = datetime.now()
                        else:
                            try:
                                t = datetime.strptime(
                                    scraped_timestamps[timestamp_id], date_fmt
                                )
                            except KeyError:
                                 t = datetime.now()

                # Grab any tags associated with the target_id
                try:
                    tag_dict = target_ids[key]["tags"]
                except KeyError:
                    tag_dict = None

                # Convert the field value to specified type within target_ids list
                data_type = target_ids[key]["data_type"]
                try:
                    corrected_value = self.convert_values(value, data_type)
                except ValueError as error:
                    print(f"WARNING: {key} not added to buffer. CAUSE: {error}")
                else:
                    # Create a metric and append it to the list to be added to the buffer
                    metric = InfluxMetric(
                        measurement=MEASUREMENT,
                        fields={key: corrected_value},
                        time=t,
                        tags=tag_dict,
                        write_precision="ns",
                    )
                    metric_list.append(metric)

        return metric_list

    async def do_work_periodically(self, update_interval=None, server_address=None):
        update_interval = update_interval or self.update_interval
        while True:
            await self.do_work(server_address=server_address)
            await asyncio.sleep(update_interval)

    async def do_work(self, message="", server_address=None):
        server_address = server_address or self.server_address

        # Get data in form of dict to load to the buffer
        metrics = self.scrape_to_metric(server_address=server_address)

        # Add to input buffer
        if metrics:
            try:
                #   # If Buffer type, use put method to ensure dequeue is used from correct side
                self._buffer.put(metrics)
            except AttributeError:
                self._buffer.append(metrics)
