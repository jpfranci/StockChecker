from datetime import datetime
from typing import Optional

from model.website import Website
from stock_checkers.stock_check_result import StockCheckResult


class Item:
    def __init__(self,
                 url: str,
                 website: Website,
                 stock_status: bool,
                 last_stock_check: datetime,
                 item_name: str,
                 last_stock_check_result: Optional[StockCheckResult]):
        self.url = url
        self.website = website
        self.stock_status = stock_status
        self.last_stock_check = last_stock_check
        self.item_name = item_name
        self.last_stock_check_result = last_stock_check_result

    def __hash__(self):
        return hash((self.url, self.website, self.stock_status, self.last_stock_check))

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.url == other.url and \
               self.website == other.website and \
               self.stock_status == other.stock_status and \
               self.last_stock_check == other.last_stock_check
