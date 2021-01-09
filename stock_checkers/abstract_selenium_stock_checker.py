from stock_checkers.abstract_stock_checker import AbstractStockChecker
from stock_checkers.stock_check_result import StockCheckResult

class AbstractSeleniumStockChecker(AbstractStockChecker):
    def wait_for_page_rendered(self, driver):
        pass

    def check_stock(self, driver, item_url) -> StockCheckResult:
        pass