import logging
import traceback

import aiohttp
import lxml.html

from conversions.price_formatters import extract_price
from stock_checkers.abstract_request_stock_checker import AbstractRequestStockChecker
from stock_checkers.stock_check_result import StockCheckResult

class EVGAStockChecker(AbstractRequestStockChecker):
    def to_stock_check_url(self, url: str, domain: str, suffix: str):
        return url

    @staticmethod
    def get_price(doc) -> float:
        whole_number_portion = doc.xpath("//span[@id='LFrame_spanFinalPrice']//strong")[0].text
        decimal_portion = doc.xpath("//span[@id='LFrame_spanFinalPrice']//sup")[0].text
        return extract_price(f'{whole_number_portion}{decimal_portion}')

    @staticmethod
    def get_is_in_stock(doc) -> bool:
        return not not doc.xpath("//a[@id='LFrame_btnAddToCart']")

    async def check_stock(self, item_url: str) -> StockCheckResult:
        stock_check_result = StockCheckResult.create_default(item_url)
        session = aiohttp.ClientSession()
        try:
            response_text = await self.fetch(session, item_url)
            doc = lxml.html.fromstring(response_text)
            stock_check_result.set_all_prices(self.get_price(doc))
            stock_check_result.is_in_stock = self.get_is_in_stock(doc)
            stock_check_result.is_item_available = True
        except Exception as e:
            logging.error(traceback.format_exc())
            logging.error(e)
        finally:
            await session.close()

        return stock_check_result
