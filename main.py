#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Created By  : Matthew Davidson
# Created Date: 2023-01-23
# version ='1.0'
# ---------------------------------------------------------------------------
"""a_short_project_description"""
# ---------------------------------------------------------------------------
from html_scraper_agent import HTMLScraperAgent
import asyncio

def main():
    buffer = []
    scraper = HTMLScraperAgent(buffer)
    asyncio.run(scraper.do_work(server_address = "./config/test.html"))
    print(scraper._buffer)


if __name__ == "__main__":
    main()
