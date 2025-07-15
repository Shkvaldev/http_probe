import os
import re
import logging
import asyncio
import aiohttp

from typing import List

from profiler import Profiler

def is_valid_url(url) -> bool:
    """Check if provided URL is valid"""
    pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'[-\w@:%._\+~#=]+'  # domain name (with letters, digits, -, _, etc.)
        r'\.[a-zа-яё]{2,6}'  # top-level domain
        r'(?:[/?][-\wа-яё@:%_\+.~#?&//=]*)?$',  # optional path/query
        re.IGNORECASE | re.UNICODE)
    return pattern.match(url) is not None

def parse_hosts_file(file_path: str) -> List[str] | None:
    """Gets URLs from provided file"""
    if not os.path.exists(file_path):
        raise ValueError("file with hosts was not found!")

    with open(file_path, "r") as file:
        content = file.readlines()
    
    urls = []
    for url in content:
        target = url.replace("\n", "")
        if is_valid_url(target):
            logging.debug(f"`{target}` successfully added")
            urls.append(target)
        else:
            logging.warning(f"URL `{target}` from file is invalid!")
    return urls

def parse_hosts(entry: str) -> List[str] | None:
    """Gets URLs from string"""
    targets = entry.split(",")
    urls = []
    for url in targets:
        if is_valid_url(url):
            logging.debug(f"`{url}` successfully added")
            urls.append(url)
        else:
            logging.warning(f"URL `{url}` is invalid!")
    return urls


async def make_test(url: str, queue: asyncio.Queue, profiler: Profiler, **kwargs) -> None:
    """Performing URL availability test"""
    record = {
        "is_success": False,
        "is_failed": False,
        "is_error": True,
        "elapsed_time": 0
    }
    start_time = asyncio.get_event_loop().time()
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url=url, **kwargs) as response:
                stop_time = asyncio.get_event_loop().time()
                record["elapsed_time"] = stop_time - start_time
                if response.status in [400, 500]:
                    record["is_failed"] = True
                    record["is_error"] = False
                    await profiler.add_record(url=url, record=record)
                    logging.debug(f"Test for `{url}` is failed (got HTTP 400 or 500)")
                else:
                    record["is_success"] = True
                    record["is_error"] = False
                    await profiler.add_record(url=url, record=record)
                    logging.debug(f"Test for `{url}` is successful")
                await queue.put(1)
    except Exception as e:
        logging.error(f"Test for `{url}` is failed: {e}")
        await profiler.add_record(url=url, record=record)
        await queue.put(1)