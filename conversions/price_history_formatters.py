from typing import Dict, List
import pytz
pacific_dt = pytz.timezone('US/Pacific')
from model.price_history import PriceHistory

def format_price_history(item_url: str, price_histories: Dict[str, List[PriceHistory]]) -> str:
    if item_url in price_histories:
        price_history_str = ""
        for price_history in price_histories[item_url]:
            price_history_str += price_history.format_message(pacific_dt)
            price_history_str += "\n"
        return f"History:\n{price_history_str}\n"
    else:
        return "No Price History Yet\n\n"