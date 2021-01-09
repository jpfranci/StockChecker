import argparse
import re
from typing import List
def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

def str2size(v):
    v = v.replace(",", "")
    if isinstance(v, int):
        return v
    size_lower = v.lower().strip()
    if len(size_lower.split(" ")) > 1:
        return size_lower
    if starts_with_size(size_lower, ["xxs", "2xs", "extra extra small"]):
        return "xxs"
    elif starts_with_size(size_lower, ["extra-small", "extra small", "xs"]):
        return "xs"
    elif starts_with_size(size_lower, ["small", "s"]):
        return "s"
    elif starts_with_size(size_lower, ["medium", "m"]):
        return 'm'
    elif starts_with_size(size_lower, ["large", "l"]):
        return "l"
    elif starts_with_size(size_lower, ["extra large", "extra-large", "xl", "1xl", "1x"]):
        return "xl"
    elif starts_with_size(size_lower, ["extra extra large", "xxl", "2xl", "2x"]):
        return "xxl"
    else:
        return size_lower

def starts_with_size(size_lower: str, size_name_variations: List[str]) -> bool:
    return any(size_lower.startswith(size_name_variation) for size_name_variation in size_name_variations)

def get_float_from_price_str(price_str: str) -> float:
    return float(re.search(r"\d+([,]\d+)*([.]\d+)?", price_str).group().replace(",", ""))