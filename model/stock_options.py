import math
from typing import List, Iterable


class StockOptions:
    def __init__(self, price_threshold: float, official_sites_only: bool, size_requirement: List[str]):
        self.price_threshold = price_threshold
        self.official_sites_only = official_sites_only
        self.size_requirement = size_requirement

    def set_size_requirement(self, size_requirement: Iterable[str]):
        self.size_requirement = list(size_requirement)

    @classmethod
    def from_json(cls, data):
        return cls(**data)

    @staticmethod
    def create_default():
        return StockOptions(
            math.inf,
            True,
            [])