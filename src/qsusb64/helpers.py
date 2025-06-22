"""Helpers."""

import asyncio
from aiohttp.client import ClientSession
from json import loads
from colorama import init as colorama_init
from colorama import Fore


def listen(host: str) -> None:
    """Keep on polling qsusb inteface and pring."""

    async def listen_task() -> None:
        """Keep on polling "http://192.168.1.8:2020/&listen" and print on the console."""
        async with ClientSession() as session:
            while True:
                try:
                    async with session.get(f"http://{host}:2020/&listen") as response:
                        if response.status == 200:
                            data = loads(await response.text())
                            print(f" {Fore.LIGHTBLUE_EX}> {data}")
                        else:
                            print(f"Failed to connect. Status code: {response.status}")
                except Exception as e:
                    print(f"Error: {e}")

    asyncio.create_task(listen_task())


colorama_init(autoreset=True)
