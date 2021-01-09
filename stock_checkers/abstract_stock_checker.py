class AbstractStockChecker:
    def to_stock_check_url(self, url: str, domain: str, suffix: str):
        pass

    def get_item_name(self, driver) -> str:
        pass

    async def get_item_name_from_url(self, url, executor):
        return ""