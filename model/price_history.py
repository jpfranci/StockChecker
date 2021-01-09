from datetime import datetime

import tldextract

from conversions.size_formatters import get_size_requirement_str
from model.stock_options import StockOptions
from model.website import Website
from stock_checkers.stock_check_result import StockCheckResult

class PriceHistory:
    def __init__(self, stock_check_result: StockCheckResult, stock_check_time: datetime):
        self.stock_check_result: StockCheckResult = stock_check_result
        self.stock_check_time: datetime = stock_check_time

    def format_message(self, timezone):
        localized_datetime_str = self.stock_check_time.astimezone(timezone).strftime("%m/%d/%Y, %I:%M %p")
        if not self.stock_check_result.is_in_stock:
            return f"{localized_datetime_str} - Not in stock"
        else:
            price_str = f"min price: {self.stock_check_result.stock_price.min_price_str}"
            if self.stock_check_result.stock_price.min_official_price_str != "":
                price_by_website_str = f"min price ({PriceHistory.url_to_website(self.stock_check_result.item_url).value}): {self.stock_check_result.stock_price.min_official_price_str}"
                if self.stock_check_result.stock_price.min_official_price_str == self.stock_check_result.stock_price.min_price_str:
                    price_str = price_by_website_str
                else:
                    price_str += f", {price_by_website_str}"

            in_stock_sizes_str = f", in-stock sizes: {get_size_requirement_str(self.stock_check_result.in_stock_sizes, False)}" if self.stock_check_result.in_stock_sizes else ""
            in_stock_stores_str = "" if not self.stock_check_result.in_stock_stores else f", in-stock location(s): {', '.join(self.stock_check_result.in_stock_stores)}"
            return f"{localized_datetime_str} - {price_str}{in_stock_sizes_str}{in_stock_stores_str}"

    @staticmethod
    def url_to_website(url: str) -> Website:
        return Website(tldextract.extract(url).domain)