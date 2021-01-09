from conversions.conversions import str2size
from conversions.size_formatters import get_size_requirement_str
from model.stock_options import StockOptions
from stock_checkers.stock_price import StockPrice
from typing import List
import json
import logging
from typing import Union, Final

MAX_FAILURES: Final = 3
# Constant to use for websites where sizes are not displayed when not in stock
# In this case, we shouldn't try to verify the user inputted sizes
NO_IN_STOCK_SIZES: Final = ['*']

class StockCheckResult:
    def __init__(self,
                 is_item_available: Union[bool, int],
                 item_name: str,
                 item_url: str,
                 stock_price: StockPrice,
                 is_in_stock: Union[bool, int],
                 available_sizes: List[str] = None,
                 in_stock_sizes: List[str] = None,
                 in_stock_stores: List[str] = None,
                 fail_count = 0):
        self.is_item_available = bool(is_item_available)
        self.item_name = item_name
        self.item_url = item_url
        self.stock_price = stock_price
        self.is_in_stock = bool(is_in_stock)
        self.available_sizes = [] if available_sizes is None else available_sizes
        self.in_stock_sizes = [] if in_stock_sizes is None else in_stock_sizes
        self.in_stock_stores = [] if in_stock_stores is None else in_stock_stores
        self.fail_count = fail_count

    def set_all_official_prices(self, price: float):
        self.stock_price.min_official_price = price
        self.stock_price.min_official_price_str = f"${price:.2f}"

    def set_all_unofficial_prices(self, price: float):
        self.stock_price.min_price = price
        self.stock_price.min_price_str = f"${price:.2f}"

    def set_all_prices(self, price: float):
        self.set_all_unofficial_prices(price)
        self.set_all_official_prices(price)

    def __hash__(self):
        return hash((self.is_item_available, self.item_url, self.stock_price, self.is_in_stock, self.available_sizes, self.in_stock_sizes, self.in_stock_stores))

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.item_url == other.item_url and \
               self.stock_price == other.stock_price and \
               self.is_in_stock == other.is_in_stock and \
               set(self.available_sizes) == set(other.available_sizes) and \
               set(self.in_stock_sizes) == set(other.in_stock_sizes) and \
               set(self.in_stock_stores) == set(other.in_stock_stores)

    def add_size_to_available(self, size: str):
        self.available_sizes.append(str2size(size))

    def add_size_to_in_stock(self, size: str):
        self.in_stock_sizes.append(str2size(size))

    @classmethod
    def from_json(cls, data: dict):
        stock_price_dict = data["stock_price"]
        stock_price = StockPrice.from_json(stock_price_dict)
        data_with_stock_price = data.copy()
        data_with_stock_price["stock_price"] = stock_price
        return cls(**data_with_stock_price)

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__)

    def format_log(self):
        available_sizes = get_size_requirement_str(self.available_sizes, False)
        in_stock_sizes = get_size_requirement_str(self.in_stock_sizes, False)
        logging.info(
            f"For item {self.item_url} and name {self.item_name}, it is in {self.is_item_available} availability with price " + \
            f"{self.stock_price.min_price_str} and official price {self.stock_price.min_official_price_str} and is in {self.is_in_stock} stock " + \
            f"with available sizes {available_sizes} and in stock sizes {in_stock_sizes}" + \
            f"and in stores {', '.join(self.in_stock_stores)}"
        )

    @staticmethod
    def create_default(item_url):
        return StockCheckResult(
            False,
            "",
            item_url,
            StockPrice.create_default(),
            False)