from typing import Optional, List, Set, Iterable

from model.stock_options import StockOptions

class NotificationUser:
    def __init__(self, id: int, stock_options: StockOptions, last_stock_status: bool, item_url: str, item_name: Optional[str] = None, last_in_stock_sizes_for_user: List[str] = None, last_in_stock_stores_for_user: List[str] = None):
        self.id = id
        self.stock_options = stock_options
        self.last_stock_status = last_stock_status
        self.item_url = item_url
        self.item_name = item_name
        self.last_in_stock_sizes_for_user = [] if last_in_stock_sizes_for_user is None else last_in_stock_sizes_for_user
        self.last_in_stock_stores_for_user = [] if last_in_stock_stores_for_user is None else last_in_stock_stores_for_user

    def set_last_in_stock_sizes_for_user(self, last_in_stock_sizes_for_user: Iterable[str]):
        self.last_in_stock_sizes_for_user = list(last_in_stock_sizes_for_user)

    def set_last_in_stock_stores_for_user(self, last_in_stock_stores_for_user: Iterable[str]):
        self.last_in_stock_stores_for_user = list(last_in_stock_stores_for_user)

    def __hash__(self):
        return hash((self.id, self.item_url))

    def __eq__(self, other):
        if not isinstance(other, type(self)): return NotImplemented
        return self.id == other.id and self.item_url == other.item_url
