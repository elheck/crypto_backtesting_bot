from abc import ABC, abstractmethod
from enum import IntEnum, unique, auto
from typing import Iterable
from pandas import DataFrame


@unique
class Signal(IntEnum):
    sell = auto()
    buy = auto()
    none = auto()


BUY_SELL = "buy_sell"


class BaseIndicator(ABC):

    def __init__(self):
        self._is_configured = False

    @abstractmethod
    def __repr__(self):
        """string representation"""

    @abstractmethod
    def calculate(self, data: Iterable) -> DataFrame:
        """configures and runs the indicator"""

    @abstractmethod
    def get_signal(self, data: Iterable) -> Signal:
        """runs the indicator"""

    @property
    def is_configured(self):
        return self._is_configured
