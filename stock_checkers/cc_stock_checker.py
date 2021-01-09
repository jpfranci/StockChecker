import logging
import re
import traceback

import aiohttp
import lxml.html

from conversions.conversions import get_float_from_price_str
from model.user_exception import UserException
from stock_checkers.abstract_request_stock_checker import AbstractRequestStockChecker
from stock_checkers.stock_check_result import StockCheckResult

base_headers = {
    'DNT': "1",
    "Cache-Control": "max-age=0",
    "Upgrade-Insecure-Requests": "1",
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-User': '?1',
    'Sec-Fetch-Dest': 'document',
    'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8'
}

class CanadaComputersStockChecker(AbstractRequestStockChecker):
    def to_stock_check_url(self, url: str, domain: str, suffix: str):
        try:
            return f'https://www.canadacomputers.com/product_info.php?cPath=13&item_id={CanadaComputersStockChecker.get_sku(url)}'
        except:
            raise UserException("The url was invalid.")

    def get_base_headers(self) -> dict:
        return base_headers

    def get_item_name(self, doc) -> str:
        item_name = super().get_item_name(doc)
        if item_name in "Welcome - Canada Computers & Electronics":
            return ""
        else:
            return item_name

    @staticmethod
    def get_sku(url):
        return re.search(r"item_id=\w*", url).group().split("item_id=")[1]

    @staticmethod
    def assert_is_item(doc):
        # checking if id codes exist
        if not doc.xpath("//p[contains(@class, 'm-0 text-small')]"):
            raise Exception("The item was not valid")

    @staticmethod
    def get_in_stock_by_store_name(doc, attribute_name: str, store_name: str):
        try:
            element = doc.xpath(f"//{attribute_name}[text() = '{store_name}']/../../..//span[@class = 'stocknumber']")[0]
            if element.text:
                stock_str = element.text.strip()
            else:
                stock_str = element.xpath(".//strong")[0].text.strip()
            stock_count = int(stock_str.split('+')[0])
            return stock_count > 0
        except:
            return False

    @staticmethod
    def get_price(doc):
        price_str = doc.xpath("//div[contains(@class, 'order-md-1')]//strong")[-1].text.strip()
        price = get_float_from_price_str(price_str)
        return price

    async def check_stock(self, item_url: str) -> StockCheckResult:
        stores_to_check = [{'store_location': 'Burnaby', 'attribute_name': 'a'},
                           {'store_location': 'Coquitlam', 'attribute_name': 'a'},
                           {'store_location': 'Grandview', 'attribute_name': 'a'},
                           {'store_location': 'Richmond', 'attribute_name': 'a'},
                           {'store_location': 'Vancouver Broadway', 'attribute_name': 'a'},
                           {'store_location': 'Online Store', 'attribute_name': 'p'}]

        stock_check_result = StockCheckResult.create_default(item_url)
        session = aiohttp.ClientSession()

        try:
            request_response = await self.fetch(session, item_url)
            doc = lxml.html.fromstring(request_response)
            self.assert_is_item(doc)
            stock_check_result.item_name = self.get_item_name(doc)
            stock_check_result.is_item_available = True
            price = CanadaComputersStockChecker.get_price(doc)
            stock_check_result.set_all_prices(price)
            for store in stores_to_check:
                in_stock = CanadaComputersStockChecker.get_in_stock_by_store_name(doc, store['attribute_name'], store['store_location'])
                if in_stock:
                    stock_check_result.is_in_stock = True
                    stock_check_result.in_stock_stores.append(store['store_location'])

        except Exception as e:
            logging.error(traceback.format_exc())
            logging.error(e)
        finally:
            await session.close()

        return stock_check_result