import pandas as pd
from ..database import get_conn
from ..strategies.base import BaseStrategy

INITIAL_CAPITAL = 1_000_000  # 初始資金 100 萬


def run_backtest(code: str, start: str, end: str, strategy: BaseStrategy) -> dict:
    # 1. 從 DB 讀取日K
    conn = get_conn()
    df = pd.read_sql_query(
        """
        SELECT date AS ts, open, high, low, close, volume
        FROM daily_kbars
        WHERE code = ? AND date BETWEEN ? AND ?
        ORDER BY date
        """,
        conn,
        params=(code, start, end),
    )
    conn.close()

    if df.empty:
        return {"error": "無資料，請確認股票代號與日期區間"}

    # 2. 產生訊號
    df = strategy.generate_signals(df)

    # 3. 模擬交易（一次只持有一個部位，不做空）
    capital = float(INITIAL_CAPITAL)
    shares  = 0
    trades  = []
    equity_curve = []
    entry_price  = 0.0

    for _, row in df.iterrows():
        price = float(row["close"])

        if row["signal"] == "BUY" and shares == 0:
            # 台股 1 張 = 1000 股；盡量買整張，不足則買零股
            lots = int(capital / (price * 1000))
            shares = lots * 1000 if lots > 0 else int(capital / price)
            cost   = shares * price
            capital -= cost
            entry_price = price
            trades.append({
                "date":       row["ts"],
                "action":     "BUY",
                "price":      price,
                "shares":     shares,
                "value":      round(cost, 0),
                "profit":     None,
                "profit_pct": None,
                "reason":     row["reason"],
            })

        elif row["signal"] == "SELL" and shares > 0:
            revenue    = shares * price
            profit     = revenue - entry_price * shares
            profit_pct = profit / (entry_price * shares) * 100
            capital   += revenue
            trades.append({
                "date":       row["ts"],
                "action":     "SELL",
                "price":      price,
                "shares":     shares,
                "value":      round(revenue, 0),
                "profit":     round(profit, 0),
                "profit_pct": round(profit_pct, 2),
                "reason":     row["reason"],
            })
            shares = 0
            entry_price = 0.0

        total_value = capital + shares * price
        equity_curve.append({"date": row["ts"], "value": round(total_value, 0)})

    # 4. 績效指標
    final_value  = capital + shares * float(df.iloc[-1]["close"])
    total_return = (final_value - INITIAL_CAPITAL) / INITIAL_CAPITAL * 100

    sell_trades  = [t for t in trades if t["action"] == "SELL"]
    win_trades   = [t for t in sell_trades if (t["profit"] or 0) > 0]
    win_rate     = len(win_trades) / len(sell_trades) * 100 if sell_trades else 0.0

    # 最大回撤
    peak = INITIAL_CAPITAL
    max_dd = 0.0
    for e in equity_curve:
        if e["value"] > peak:
            peak = e["value"]
        dd = (e["value"] - peak) / peak * 100
        if dd < max_dd:
            max_dd = dd

    # 5. 回傳
    kbars = df[["ts", "open", "high", "low", "close", "volume"]].to_dict("records")

    return {
        "kbars":        kbars,
        "trades":       trades,
        "equity_curve": equity_curve,
        "metrics": {
            "initial_capital": INITIAL_CAPITAL,
            "final_value":     round(final_value, 0),
            "total_return":    round(total_return, 2),
            "max_drawdown":    round(max_dd, 2),
            "win_rate":        round(win_rate, 2),
            "total_trades":    len(sell_trades),
            "winning_trades":  len(win_trades),
        },
    }
