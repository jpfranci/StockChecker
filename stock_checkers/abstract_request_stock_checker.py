import logging
import traceback

import aiohttp
from aiohttp import ClientSession
import asyncio

from model.user_exception import UserException
from stock_checkers.abstract_stock_checker import AbstractStockChecker
from stock_checkers.stock_check_result import StockCheckResult
import lxml.html

from services.user_agent_service import get_random_user_agent

base_headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'none',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
}

class AbstractRequestStockChecker(AbstractStockChecker):
    def get_base_headers(self) -> dict:
        return base_headers

    def get_item_name(self, doc) -> str:
        return doc.find(".//title").text.strip()

    def get_item_name_thread(self, response) -> str:
        doc = lxml.html.fromstring(response)
        return self.get_item_name(doc)

    async def get_item_name_from_url(self, url, executor):
        session = aiohttp.ClientSession()
        item_name = ""
        try:
            response = await self.fetch(session, url)
            loop = asyncio.get_running_loop()
            item_name = await loop.run_in_executor(executor, self.get_item_name_thread, response)
        except Exception as e:
            logging.error(traceback.format_exc())
            logging.error(e)
            raise UserException(f"Could not subscribe to {url}, it was invalid")
        finally:
            session.cookie_jar.clear()
            await session.close()

        return item_name

    def get_headers(self) -> dict:
        return self.with_user_agent(self.get_base_headers().copy())

    def with_user_agent(self, headers) -> dict:
        headers_copy = headers.copy()
        headers_copy["user-agent"] = get_random_user_agent()
        return headers_copy

    async def check_stock(self, item_url: str) -> StockCheckResult:
        pass

    async def fetch(self, session: ClientSession, url, header_override = None):
        timeout = aiohttp.ClientTimeout(total=100)
        headers = header_override if header_override is not None else self.get_headers()
        async with session.get(url, headers=headers, timeout=timeout) as response:
            try:
                text = await response.text()
                response.raise_for_status()
                return text
            except Exception as e:
                logging.error(text)
                logging.error(traceback.format_exc())
                logging.error(e)
                raise e

    async def post(self, session: ClientSession, url, data, header_override = None):
        timeout = aiohttp.ClientTimeout(total=100)
        headers = header_override if header_override is not None else self.get_headers()
        async with session.post(url, data=data, headers=headers, timeout=timeout) as response:
            try:
                text = await response.text()
                response.raise_for_status()
                return text
            except Exception as e:
                logging.error(text)
                logging.error(traceback.format_exc())
                logging.error(e)
                raise e