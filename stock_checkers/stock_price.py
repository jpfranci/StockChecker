import math

class StockPrice:
    def __init__(self, min_price: float, min_price_str: str, min_official_price: float, min_official_price_str: str):
        self.min_price = min_price
        self.min_price_str = min_price_str
        self.min_official_price = min_official_price
        self.min_official_price_str = min_official_price_str

    def __hash__(self):
        return hash((self.min_price, self.min_price_str, self.min_official_price, self.min_official_price_str))

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.min_price_str == other.min_price_str and self.min_official_price_str == other.min_official_price_str

    @classmethod
    def from_json(cls, data: dict):
        return cls(**data)

    @staticmethod
    def create_default():
        return StockPrice(
            math.inf,
            "",
            math.inf,
            "")