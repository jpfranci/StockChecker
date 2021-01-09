import re

def extract_price(price_str) -> float:
    return float(re.search(r"\d+([,]\d+)*([.]\d+)?", price_str).group().replace(",", ""))