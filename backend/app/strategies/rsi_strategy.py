import pandas as pd
from .base import BaseStrategy


class RSIStrategy(BaseStrategy):
    id = "rsi"
    name = "RSI 超買超賣"
    description = "RSI 從超賣區回升時買入，從超買區回落時賣出"
    params_schema = [
        {"key": "period",     "label": "RSI 週期", "type": "int", "default": 14, "min": 2,  "max": 50, "step": 1},
        {"key": "oversold",   "label": "超賣門檻", "type": "int", "default": 30, "min": 10, "max": 45, "step": 1},
        {"key": "overbought", "label": "超買門檻", "type": "int", "default": 70, "min": 55, "max": 90, "step": 1},
    ]

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        period     = int(self.params["period"])
        oversold   = self.params["oversold"]
        overbought = self.params["overbought"]

        df = df.copy()
        delta = df["close"].diff()
        gain  = delta.clip(lower=0).rolling(period).mean()
        loss  = (-delta.clip(upper=0)).rolling(period).mean()
        rs    = gain / loss.replace(0, float("inf"))
        df["rsi"]      = 100 - 100 / (1 + rs)
        df["_prev_rsi"] = df["rsi"].shift(1)

        df["signal"] = None
        df["reason"] = None

        buy  = (df["rsi"] > oversold)   & (df["_prev_rsi"] <= oversold)
        sell = (df["rsi"] < overbought) & (df["_prev_rsi"] >= overbought)

        df.loc[buy,  "signal"] = "BUY"
        df.loc[buy,  "reason"] = df[buy].apply(
            lambda r: f"RSI({period}) = {r['rsi']:.1f} 從超賣區({oversold})回升", axis=1
        )
        df.loc[sell, "signal"] = "SELL"
        df.loc[sell, "reason"] = df[sell].apply(
            lambda r: f"RSI({period}) = {r['rsi']:.1f} 從超買區({overbought})回落", axis=1
        )

        df.drop(columns=["_prev_rsi"], inplace=True)
        return df
