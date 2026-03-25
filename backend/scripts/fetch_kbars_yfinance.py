"""
用 yfinance 補全 daily_kbars 的歷史日K資料。

【重要】yfinance 與 Shioaji 資料差異：
    - OHLC 價格一致
    - volume 單位不同：Shioaji 為「張」，yfinance 為「股」（約差 1000 倍）
    - 因此本腳本【預設只補沒有任何資料的股票】，不混用兩種來源

使用方式：
    python fetch_kbars_yfinance.py                   # 預設：只補完全沒有資料的股票
    python fetch_kbars_yfinance.py --codes 2330 2317  # 指定股票（會強制覆蓋）
    python fetch_kbars_yfinance.py --limit 10         # 測試用，只抓前 10 支

注意：
    - TSE (上市) ticker 格式：{code}.TW
    - OTC (上櫃) ticker 格式：{code}.TWO
    - amount 欄位以 close * volume 估算（yfinance 無提供成交金額）
"""

import logging
import sqlite3
import time
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import yfinance as yf

# ── 設定 ──────────────────────────────────────────────────────────────────────
START_DATE = "2020-03-02"
DB_PATH    = Path(__file__).parent.parent / "data" / "stock_data.db"
LOG_PATH   = Path(__file__).parent.parent / "data" / "fetch_kbars_yfinance.log"

SLEEP_BETWEEN = 0.3   # 每支股票之間的間隔秒數，避免被封鎖

# ── Logger ────────────────────────────────────────────────────────────────────
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)


# ── 資料庫 ────────────────────────────────────────────────────────────────────
def get_last_date(conn: sqlite3.Connection, code: str) -> str | None:
    row = conn.execute(
        "SELECT MAX(date) FROM daily_kbars WHERE code = ?", (code,)
    ).fetchone()
    return row[0]


def upsert_df(conn: sqlite3.Connection, df: pd.DataFrame) -> int:
    rows = df[["code", "date", "open", "high", "low", "close", "volume", "amount"]].values.tolist()
    conn.executemany(
        """
        INSERT OR REPLACE INTO daily_kbars (code, date, open, high, low, close, volume, amount)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    conn.commit()
    return len(rows)


def get_stocks(conn: sqlite3.Connection) -> list[tuple[str, str]]:
    """回傳 [(code, exchange), ...] 清單，排除特別股"""
    rows = conn.execute(
        "SELECT code, exchange FROM stocks WHERE code NOT GLOB '*[AB]' ORDER BY code"
    ).fetchall()
    return rows


# ── yfinance 資料抓取 ─────────────────────────────────────────────────────────
def code_to_ticker(code: str, exchange: str) -> str:
    """將台股代碼轉換成 yfinance ticker"""
    suffix = ".TW" if exchange == "TSE" else ".TWO"
    return f"{code}{suffix}"


def fetch_daily(code: str, exchange: str, start: str, end: str) -> pd.DataFrame | None:
    """
    用 yfinance 抓取日K，回傳符合 DB 格式的 DataFrame。
    失敗或無資料回傳 None。
    """
    ticker = code_to_ticker(code, exchange)
    try:
        df = yf.download(
            ticker,
            start=start,
            end=end,
            auto_adjust=True,   # 自動還原權值
            progress=False,
        )

        if df.empty:
            return None

        # yfinance 回傳 MultiIndex columns 時攤平
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df = df.rename(columns={
            "Open":   "open",
            "High":   "high",
            "Low":    "low",
            "Close":  "close",
            "Volume": "volume",
        })

        df = df[["open", "high", "low", "close", "volume"]].copy()
        df["amount"] = df["close"] * df["volume"]   # 估算成交金額
        df["code"]   = code
        df.index     = df.index.strftime("%Y-%m-%d")
        df.index.name = "date"
        df = df.reset_index()

        # 過濾掉 NaN
        df = df.dropna(subset=["open", "close"])
        df["volume"] = df["volume"].fillna(0).astype(int)

        return df

    except Exception as e:
        log.error(f"{code} ({ticker}) 抓取失敗: {e}")
        return None


# ── 主程式 ────────────────────────────────────────────────────────────────────
def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="用 yfinance 補全日K資料")
    parser.add_argument("--codes", nargs="*", help="指定股票代碼，空白分隔")
    parser.add_argument("--limit", type=int, default=0, help="最多抓幾支（測試用）")
    parser.add_argument("--end", default=date.today().isoformat(), help="結束日期，預設今天")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    all_stocks = get_stocks(conn)   # [(code, exchange), ...]

    # 過濾目標股票：預設只補完全沒有資料的股票，避免與 Shioaji 資料混用
    if args.codes:
        exchange_map = {code: ex for code, ex in all_stocks}
        targets = [(c, exchange_map.get(c, "TSE")) for c in args.codes]
    else:
        existing = {r[0] for r in conn.execute("SELECT DISTINCT code FROM daily_kbars").fetchall()}
        targets = [(code, ex) for code, ex in all_stocks if code not in existing]
        log.info(f"共 {len(targets)} 支股票完全無資料，準備補全")

    if args.limit > 0:
        targets = targets[:args.limit]

    log.info(f"共 {len(targets)} 支股票待處理，結束日期: {args.end}")

    total_rows = 0
    skip_count = 0
    fail_count = 0

    for i, (code, exchange) in enumerate(targets, start=1):
        last = get_last_date(conn, code)
        if last:
            start = (date.fromisoformat(last) + timedelta(days=1)).isoformat()
        else:
            start = START_DATE

        if start > args.end:
            log.debug(f"[{i}/{len(targets)}] {code}: 已是最新，跳過")
            skip_count += 1
            continue

        df = fetch_daily(code, exchange, start, args.end)

        if df is None or df.empty:
            log.warning(f"[{i}/{len(targets)}] {code}: 無資料")
            fail_count += 1
        else:
            rows = upsert_df(conn, df)
            total_rows += rows
            log.info(f"[{i}/{len(targets)}] {code}: +{rows} 筆  累計 {total_rows} 筆")

        time.sleep(SLEEP_BETWEEN)

    conn.close()
    log.info(
        f"完成！寫入 {total_rows} 筆，跳過(已最新) {skip_count} 支，"
        f"無資料/失敗 {fail_count} 支"
    )


if __name__ == "__main__":
    main()
