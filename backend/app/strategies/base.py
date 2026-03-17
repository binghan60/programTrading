from abc import ABC, abstractmethod
import pandas as pd


class BaseStrategy(ABC):
    id: str
    name: str
    description: str
    params_schema: list  # [{key, label, type, default, min, max, step}]

    def __init__(self, params: dict):
        self.params = {p["key"]: params.get(p["key"], p["default"]) for p in self.params_schema}

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Input : df with columns [ts, open, high, low, close, volume]
        Output: same df with added columns [signal, reason]
                signal: 'BUY' | 'SELL' | None
        """
