from enum import Enum

from settings.settings import TIME_THRESHOLD_OVERRIDE_DICT, SELENIUM_TIME_THRESHOLD, REQUESTS_TIME_THRESHOLD
from stock_checkers.abstract_request_stock_checker import AbstractRequestStockChecker
from stock_checkers.abstract_selenium_stock_checker import AbstractSeleniumStockChecker
from stock_checkers.abstract_stock_checker import AbstractStockChecker
from typing import Dict

from stock_checkers.cc_stock_checker import CanadaComputersStockChecker
from stock_checkers.evga_stock_checker import EVGAStockChecker
from stock_checkers.princess_polly_stock_checker import PrincessPollyStockChecker

class Website(Enum):
    CANADACOMPUTERS = "canadacomputers"
    PRINCESSPOLLY="princesspolly"
    EVGA="evga"

def to_time_threshold_dict(website_dict_to_transform: Dict[Website, AbstractStockChecker], default_threshold: int) -> Dict[Website, int]:
    ret = {}
    for website in website_dict_to_transform:
        ret[website] = TIME_THRESHOLD_OVERRIDE_DICT.get(website.value, default_threshold)
    return ret

selenium_website_dict: Dict[Website, AbstractSeleniumStockChecker] = {}

requests_website_dict: Dict[Website, AbstractRequestStockChecker] = {
    Website.CANADACOMPUTERS: CanadaComputersStockChecker(),
    Website.PRINCESSPOLLY: PrincessPollyStockChecker(),
    Website.EVGA: EVGAStockChecker()
}

selenium_time_threshold_dict: Dict[Website, int] = to_time_threshold_dict(selenium_website_dict, SELENIUM_TIME_THRESHOLD)
requests_time_threshold_dict: Dict[Website, int] = to_time_threshold_dict(requests_website_dict, REQUESTS_TIME_THRESHOLD)
time_threshold_dict: Dict[Website, int] = {
    **selenium_time_threshold_dict,
    **requests_time_threshold_dict
}

website_dict = {
    **selenium_website_dict,
    **requests_website_dict
}

bannable_websites = [Website.CANADACOMPUTERS]