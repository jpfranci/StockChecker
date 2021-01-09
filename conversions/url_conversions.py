from typing import Tuple
import tldextract
from model.website import Website, website_dict

def to_stock_check_url(url: str) -> Tuple[str, Website]:
    domain, suffix = (tldextract.extract(url).domain, tldextract.extract(url).suffix)
    website: Website = Website(domain)
    return website_dict[website].to_stock_check_url(url, domain, suffix), website