"""
抓取全上市(TSE)、上櫃(OTC)股票歷史日K資料，存入本地 SQLite。

使用方式：
    python fetch_kbars.py

注意：
    - 第一次執行會從 START_DATE 開始抓，之後會自動抓增量（從上次最後日期繼續）
    - 速率限制：5 秒內最多 40 次請求（留 10 次緩衝）
    - 若中途中斷，重新執行會從上次中斷處繼續
"""

import os
import time
import logging
import sqlite3
from datetime import datetime, date, timedelta
from pathlib import Path

import pandas as pd
import shioaji as sj
from dotenv import load_dotenv

# ── 設定 ──────────────────────────────────────────────────────────────────────
load_dotenv(Path(__file__).parent.parent / ".env")

START_DATE = "2020-03-02"           # Shioaji 歷史資料最早起始日
DB_PATH    = Path(__file__).parent.parent / "data" / "stock_data.db"
LOG_PATH   = Path(__file__).parent.parent / "data" / "fetch_kbars.log"


RATE_LIMIT   = 30     # 每個時間窗口最多幾次請求（官方上限 50，留緩衝）
RATE_WINDOW  = 5.0    # 時間窗口秒數
CHUNK_MONTHS = 6      # 每次 API 呼叫涵蓋幾個月（避免單次請求資料量太大超時）

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
def init_db(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS daily_kbars (
            code    TEXT NOT NULL,
            date    TEXT NOT NULL,
            open    REAL,
            high    REAL,
            low     REAL,
            close   REAL,
            volume  INTEGER,
            amount  REAL,
            PRIMARY KEY (code, date)
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_code ON daily_kbars (code)")
    conn.commit()


def get_last_date(conn: sqlite3.Connection, code: str) -> str | None:
    """回傳該股票在 DB 中最後一筆日期字串，無資料則回傳 None。"""
    row = conn.execute(
        "SELECT MAX(date) FROM daily_kbars WHERE code = ?", (code,)
    ).fetchone()
    return row[0]


def upsert_df(conn: sqlite3.Connection, df: pd.DataFrame) -> int:
    """將 DataFrame 批次 upsert 進 daily_kbars，回傳寫入筆數。"""
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


# ── Shioaji 資料抓取 ───────────────────────────────────────────────────────────
class RateLimiter:
    """滑動窗口速率限制器"""
    def __init__(self, max_calls: int, period: float) -> None:
        self.max_calls = max_calls
        self.period    = period
        self.calls: list[float] = []

    def wait(self) -> None:
        now = time.time()
        # 移除窗口外的舊記錄
        self.calls = [t for t in self.calls if now - t < self.period]
        if len(self.calls) >= self.max_calls:
            sleep_time = self.period - (now - self.calls[0]) + 0.05
            if sleep_time > 0:
                time.sleep(sleep_time)
        self.calls.append(time.time())


def date_chunks(start: str, end: str, months: int) -> list[tuple[str, str]]:
    """將日期區間切成數個小區間，每段 months 個月。"""
    from dateutil.relativedelta import relativedelta

    chunks = []
    cur = date.fromisoformat(start)
    end_date = date.fromisoformat(end)
    while cur <= end_date:
        chunk_end = min(cur + relativedelta(months=months) - timedelta(days=1), end_date)
        chunks.append((cur.isoformat(), chunk_end.isoformat()))
        cur = chunk_end + timedelta(days=1)
    return chunks


def fetch_daily(api: sj.Shioaji, limiter: RateLimiter, code: str, start: str, end: str) -> pd.DataFrame | None:
    """
    呼叫 api.kbars 取得分鐘線，resample 成日K後回傳 DataFrame。
    若無資料或失敗則回傳 None。
    """
    try:
        contract = api.Contracts.Stocks[code]
        if contract is None:
            log.warning(f"{code}: 找不到合約")
            return None

        limiter.wait()
        kbars = api.kbars(contract=contract, start=start, end=end)

        if not kbars.ts:
            return None

        df = pd.DataFrame({**kbars})
        df["ts"] = pd.to_datetime(df["ts"])
        df = df.set_index("ts")

        # 分鐘線 → 日線
        daily = df.resample("1D").agg(
            open=("Open", "first"),
            high=("High", "max"),
            low=("Low", "min"),
            close=("Close", "last"),
            volume=("Volume", "sum"),
            amount=("Amount", "sum"),
        ).dropna(subset=["open"])

        daily["code"] = code
        daily.index = daily.index.date.astype(str)   # type: ignore[attr-defined]
        daily.index.name = "date"
        return daily.reset_index()

    except Exception as e:
        log.error(f"{code} {start}~{end} 抓取失敗: {e}")
        return None


# ── 主程式 ────────────────────────────────────────────────────────────────────
def get_all_codes(conn: sqlite3.Connection) -> list[str]:
    """從 stocks 表讀取所有股票代碼（排除特別股 A/B 結尾）"""
    rows = conn.execute(
        "SELECT code FROM stocks WHERE code NOT GLOB '*[AB]' ORDER BY code"
    ).fetchall()
    return [r[0] for r in rows]


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="抓取日K資料")
    parser.add_argument("--codes", nargs="*", help="指定股票代碼，空白分隔；不填則抓全部")
    parser.add_argument("--limit", type=int, default=0, help="最多抓幾支（測試用，0=不限制）")
    parser.add_argument("--end", help="指定中止日期 (YYYY-MM-DD)，不填則自動判斷")
    args = parser.parse_args()

    # 登入（先連 DB 再登入，避免登入後等待太久）
    conn = sqlite3.connect(DB_PATH)
    init_db(conn)

    if args.codes:
        all_codes = args.codes
    else:
        all_codes = get_all_codes(conn)

    if args.limit > 0:
        all_codes = all_codes[:args.limit]

    log.info(f"共 {len(all_codes)} 支股票待處理")

    api = sj.Shioaji(simulation=True)
    api.login(
        api_key=os.environ["API_KEY"],
        secret_key=os.environ["SECRET_KEY"],
        contracts_timeout=30000,
        fetch_contract=True,
    )
    log.info("Shioaji 登入成功")

    limiter = RateLimiter(max_calls=RATE_LIMIT, period=RATE_WINDOW)
    
    # 決定抓取的終點日期
    if args.end:
        today = args.end
        log.info(f"使用指定中止日期: {today}")
    else:
        # 自動判斷 (今日或最後一個交易日)
        now = datetime.now()
        # 台灣股市 13:30 收盤，考慮資料整理延遲，15:00 後才抓當天資料
        fetch_date = now.date() if now.hour >= 15 else now.date() - timedelta(days=1)
        # 排除週末
        while fetch_date.weekday() >= 5:
            fetch_date -= timedelta(days=1)
        today = fetch_date.isoformat()
        log.info(f"自動判定中止日期: {today}")

    total_rows = 0
    for i, code in enumerate(all_codes, start=1):
        # 決定起始日（增量更新）
        last = get_last_date(conn, code)
        if last:
            start = (date.fromisoformat(last) + timedelta(days=1)).isoformat()
        else:
            start = START_DATE

        if start > today:
            log.debug(f"[{i}/{len(all_codes)}] {code}: 已是最新，跳過")
            continue

        # 分段抓取（每段 CHUNK_MONTHS 個月）
        chunks = date_chunks(start, today, CHUNK_MONTHS)
        stock_rows = 0
        for chunk_start, chunk_end in chunks:
            df = fetch_daily(api, limiter, code, chunk_start, chunk_end)
            if df is not None and not df.empty:
                stock_rows += upsert_df(conn, df)

        total_rows += stock_rows
        log.info(f"[{i}/{len(all_codes)}] {code}: +{stock_rows} 筆  累計 {total_rows} 筆")

    conn.close()
    api.logout()
    log.info(f"完成！共寫入 {total_rows} 筆日K資料，儲存於 {DB_PATH}")
    log.info(f"下次執行會自動從各股最後日期繼續（增量更新）")


if __name__ == "__main__":
    main()
