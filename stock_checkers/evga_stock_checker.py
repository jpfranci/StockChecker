import logging
import traceback

import aiohttp
import lxml.html

from conversions.price_formatters import extract_price
from stock_checkers.abstract_request_stock_checker import AbstractRequestStockChecker
from stock_checkers.stock_check_result import StockCheckResult

base_headers = {
    'authority': 'www.evga.com',
    'dnt': '1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'sec-fetch-user': '?1',
    'sec-fetch-site': 'none',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-dest': 'document',
    'accept-language': 'en-GB,en;q=0.9'
}

class EVGAStockChecker(AbstractRequestStockChecker):
    def to_stock_check_url(self, url: str, domain: str, suffix: str):
        return url

    def get_base_headers(self) -> dict:
        return base_headers

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
            response_text = await self.fetch(session, item_url, header_override=base_headers)
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
