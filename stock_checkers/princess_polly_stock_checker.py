import logging
import traceback

import aiohttp
import lxml.html

from conversions.conversions import str2size
from conversions.price_formatters import extract_price
from stock_checkers.abstract_request_stock_checker import AbstractRequestStockChecker
from stock_checkers.stock_check_result import StockCheckResult

class PrincessPollyStockChecker(AbstractRequestStockChecker):
    def to_stock_check_url(self, url: str, domain: str, suffix: str):
        return url.split("?")[0]

    @staticmethod
    def get_price(doc) -> float:
        return extract_price(doc.xpath("//span[@data-product-price]")[0].text)

    @staticmethod
    def get_all_available_size_elements(doc):
        return doc.xpath("//select[@id='SingleOptionSelector-1']/option[not(@disabled)]")

    async def check_stock(self, item_url: str) -> StockCheckResult:
        stock_check_result = StockCheckResult.create_default(item_url)
        session = aiohttp.ClientSession()
        try:
            response_text = await self.fetch(session, item_url)
            doc = lxml.html.fromstring(response_text)
            stock_check_result.set_all_prices(self.get_price(doc))
            stock_check_result.is_item_available = True
            available_size_elements = self.get_all_available_size_elements(doc)
            for available_size_element in available_size_elements:
                size = str2size(available_size_element.get("value"))
                stock_check_result.available_sizes.append(size)
                if "(Sold Out – Notify Me)" not in available_size_element.text:
                    stock_check_result.in_stock_sizes.append(size)
            stock_check_result.is_in_stock = not not stock_check_result.in_stock_sizes
        except Exception as e:
            logging.error(traceback.format_exc())
            logging.error(e)
        finally:
            await session.close()

        return stock_check_result