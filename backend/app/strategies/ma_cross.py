import pandas as pd
from .base import BaseStrategy


class MACrossStrategy(BaseStrategy):
    id = "ma_cross"
    name = "雙均線交叉"
    description = "短期均線上穿長期均線時買入，下穿時賣出"
    params_schema = [
        {"key": "short_period", "label": "短期均線", "type": "int", "default": 5,  "min": 2,  "max": 60,  "step": 1},
        {"key": "long_period",  "label": "長期均線", "type": "int", "default": 20, "min": 5,  "max": 200, "step": 1},
    ]

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        s = int(self.params["short_period"])
        l = int(self.params["long_period"])

        df = df.copy()
        df[f"ma{s}"] = df["close"].rolling(s).mean()
        df[f"ma{l}"] = df["close"].rolling(l).mean()
        df["_prev_s"] = df[f"ma{s}"].shift(1)
        df["_prev_l"] = df[f"ma{l}"].shift(1)

        df["signal"] = None
        df["reason"] = None

        buy  = (df[f"ma{s}"] > df[f"ma{l}"]) & (df["_prev_s"] <= df["_prev_l"])
        sell = (df[f"ma{s}"] < df[f"ma{l}"]) & (df["_prev_s"] >= df["_prev_l"])

        df.loc[buy,  "signal"] = "BUY"
        df.loc[buy,  "reason"] = df[buy].apply(
            lambda r: f"MA{s}({r[f'ma{s}']:.2f}) 上穿 MA{l}({r[f'ma{l}']:.2f})", axis=1
        )
        df.loc[sell, "signal"] = "SELL"
        df.loc[sell, "reason"] = df[sell].apply(
            lambda r: f"MA{s}({r[f'ma{s}']:.2f}) 下穿 MA{l}({r[f'ma{l}']:.2f})", axis=1
        )

        df.drop(columns=["_prev_s", "_prev_l"], inplace=True)
        return df
