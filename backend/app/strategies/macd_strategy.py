import pandas as pd
from .base import BaseStrategy


class MACDStrategy(BaseStrategy):
    id = "macd"
    name = "MACD 交叉"
    description = "MACD 線上穿訊號線時買入，下穿時賣出"
    params_schema = [
        {"key": "fast",   "label": "快線週期",  "type": "int", "default": 12, "min": 2, "max": 50,  "step": 1},
        {"key": "slow",   "label": "慢線週期",  "type": "int", "default": 26, "min": 5, "max": 100, "step": 1},
        {"key": "signal", "label": "訊號線週期", "type": "int", "default": 9,  "min": 2, "max": 50,  "step": 1},
    ]

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        fast   = int(self.params["fast"])
        slow   = int(self.params["slow"])
        signal = int(self.params["signal"])

        df = df.copy()
        ema_fast        = df["close"].ewm(span=fast,   adjust=False).mean()
        ema_slow        = df["close"].ewm(span=slow,   adjust=False).mean()
        df["macd"]      = ema_fast - ema_slow
        df["macd_sig"]  = df["macd"].ewm(span=signal, adjust=False).mean()
        df["_prev_macd"] = df["macd"].shift(1)
        df["_prev_sig"]  = df["macd_sig"].shift(1)

        df["signal"] = None
        df["reason"] = None

        buy  = (df["macd"] > df["macd_sig"]) & (df["_prev_macd"] <= df["_prev_sig"])
        sell = (df["macd"] < df["macd_sig"]) & (df["_prev_macd"] >= df["_prev_sig"])

        df.loc[buy,  "signal"] = "BUY"
        df.loc[buy,  "reason"] = df[buy].apply(
            lambda r: f"MACD({r['macd']:.3f}) 上穿 Signal({r['macd_sig']:.3f})", axis=1
        )
        df.loc[sell, "signal"] = "SELL"
        df.loc[sell, "reason"] = df[sell].apply(
            lambda r: f"MACD({r['macd']:.3f}) 下穿 Signal({r['macd_sig']:.3f})", axis=1
        )

        df.drop(columns=["_prev_macd", "_prev_sig"], inplace=True)
        return df
