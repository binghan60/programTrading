"""
抓取指定股票清單過去 3 年的分K資料，存入本地 SQLite。

使用方式：
    python fetch_minute_kbars.py

注意：
    - 分段抓取（每次 1 個月），避免單次請求資料量過大
    - 支援斷點續傳：從各股票在 DB 中的最後一筆時間戳繼續
    - 速率限制：5 秒內最多 40 次請求（官方上限 50，留緩衝）
"""

import os
import time
import logging
import sqlite3
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import shioaji as sj
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv

# ── 設定 ──────────────────────────────────────────────────────────────────────
load_dotenv(Path(__file__).parent.parent / ".env")

STOCK_LIST = [
    '1519', '1605', '2313', '2327', '2344', '2454', '2455', '2486',
    '3037', '3234', '3265', '3324', '3443', '3450', '3535', '4931',
    '4979', '5340', '6770', '6903', '8021', '8042', '8111', '8358',
    '00981A',
]

# 過去 3 年
END_DATE   = date.today().isoformat()
START_DATE = (date.today() - relativedelta(years=3)).isoformat()

DB_PATH  = Path(__file__).parent.parent / "data" / "stock_data.db"
LOG_PATH = Path(__file__).parent.parent / "data" / "fetch_minute_kbars.log"

RATE_LIMIT  = 10    # 每個窗口最多幾次 API 請求（保守設定，避免被封鎖）
RATE_WINDOW = 5.0   # 時間窗口秒數
CHUNK_MONTHS = 1    # 每次 API 呼叫涵蓋幾個月（分K資料量大，每次只抓 1 個月）

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
        CREATE TABLE IF NOT EXISTS minute_kbars (
            code    TEXT NOT NULL,
            ts      TEXT NOT NULL,
            open    REAL,
            high    REAL,
            low     REAL,
            close   REAL,
            volume  INTEGER,
            amount  REAL,
            PRIMARY KEY (code, ts)
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_minute_code ON minute_kbars (code)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_minute_ts   ON minute_kbars (ts)")
    conn.commit()


def get_last_ts(conn: sqlite3.Connection, code: str) -> str | None:
    """回傳該股票在 DB 中最後一筆時間戳（ISO 字串），無資料則回傳 None。"""
    row = conn.execute(
        "SELECT MAX(ts) FROM minute_kbars WHERE code = ?", (code,)
    ).fetchone()
    return row[0]


def upsert_df(conn: sqlite3.Connection, df: pd.DataFrame) -> int:
    """將 DataFrame 批次 upsert 進 minute_kbars，回傳寫入筆數。"""
    rows = df[["code", "ts", "open", "high", "low", "close", "volume", "amount"]].values.tolist()
    conn.executemany(
        """
        INSERT OR REPLACE INTO minute_kbars (code, ts, open, high, low, close, volume, amount)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    conn.commit()
    return len(rows)


# ── 速率限制 ──────────────────────────────────────────────────────────────────
class RateLimiter:
    """滑動窗口速率限制器"""
    def __init__(self, max_calls: int, period: float) -> None:
        self.max_calls = max_calls
        self.period    = period
        self.calls: list[float] = []

    def wait(self) -> None:
        now = time.time()
        self.calls = [t for t in self.calls if now - t < self.period]
        if len(self.calls) >= self.max_calls:
            sleep_time = self.period - (now - self.calls[0]) + 0.05
            if sleep_time > 0:
                time.sleep(sleep_time)
        self.calls.append(time.time())


# ── 日期切段 ──────────────────────────────────────────────────────────────────
def date_chunks(start: str, end: str, months: int) -> list[tuple[str, str]]:
    """將日期區間切成數個小區間，每段 months 個月。"""
    chunks = []
    cur = date.fromisoformat(start)
    end_date = date.fromisoformat(end)
    while cur <= end_date:
        chunk_end = min(cur + relativedelta(months=months) - timedelta(days=1), end_date)
        chunks.append((cur.isoformat(), chunk_end.isoformat()))
        cur = chunk_end + timedelta(days=1)
    return chunks


# ── 抓取分K ──────────────────────────────────────────────────────────────────
def fetch_minute(
    api: sj.Shioaji,
    limiter: RateLimiter,
    code: str,
    start: str,
    end: str,
) -> pd.DataFrame | None:
    """
    呼叫 api.kbars 取得 1 分鐘 K 線，回傳整理後的 DataFrame。
    若無資料或失敗則回傳 None。
    """
    try:
        contract = api.Contracts.Stocks[code]
        if contract is None:
            log.warning(f"{code}: 找不到合約（可能不是一般股票，跳過）")
            return None

        limiter.wait()
        kbars = api.kbars(contract=contract, start=start, end=end)

        if not kbars.ts:
            print(f"⚠️  [{code}] {start}~{end} 回傳空陣列，可能已被封鎖或該期間無資料！")
            return None

        df = pd.DataFrame({**kbars})
        df["ts"] = pd.to_datetime(df["ts"]).dt.strftime("%Y-%m-%d %H:%M:%S")
        df = df.rename(columns={
            "Open": "open", "High": "high", "Low": "low",
            "Close": "close", "Volume": "volume", "Amount": "amount",
        })
        df["code"] = code
        return df[["code", "ts", "open", "high", "low", "close", "volume", "amount"]]

    except Exception as e:
        log.error(f"{code} {start}~{end} 抓取失敗: {e}")
        return None


# ── 主程式 ────────────────────────────────────────────────────────────────────
def main() -> None:
    api = sj.Shioaji(simulation=True)
    api.login(
        api_key=os.environ["API_KEY"],
        secret_key=os.environ["SECRET_KEY"],
        contracts_timeout=30000,
        fetch_contract=True,
    )
    log.info("Shioaji 登入成功")
    log.info(f"資料區間：{START_DATE} ~ {END_DATE}")
    log.info(f"股票清單（{len(STOCK_LIST)} 支）：{STOCK_LIST}")

    conn = sqlite3.connect(DB_PATH)
    init_db(conn)
    limiter = RateLimiter(max_calls=RATE_LIMIT, period=RATE_WINDOW)

    total_rows = 0
    for i, code in enumerate(STOCK_LIST, start=1):
        # 斷點續傳：從 DB 最後一筆時間戳的隔天開始
        last_ts = get_last_ts(conn, code)
        if last_ts:
            last_date = last_ts[:10]   # "YYYY-MM-DD HH:MM:SS" → "YYYY-MM-DD"
            start = (date.fromisoformat(last_date) + timedelta(days=1)).isoformat()
            log.info(f"[{i}/{len(STOCK_LIST)}] {code}: 續傳，從 {start} 開始")
        else:
            start = START_DATE
            log.info(f"[{i}/{len(STOCK_LIST)}] {code}: 全新抓取，從 {start} 開始")

        if start > END_DATE:
            log.info(f"[{i}/{len(STOCK_LIST)}] {code}: 資料已是最新，跳過")
            continue

        # 分段抓取（每段 CHUNK_MONTHS 個月）
        chunks = date_chunks(start, END_DATE, CHUNK_MONTHS)
        stock_rows = 0
        for j, (chunk_start, chunk_end) in enumerate(chunks, start=1):
            log.info(f"  {code} 第 {j}/{len(chunks)} 段：{chunk_start} ~ {chunk_end}")
            df = fetch_minute(api, limiter, code, chunk_start, chunk_end)
            if df is not None and not df.empty:
                written = upsert_df(conn, df)
                stock_rows += written
                log.info(f"    寫入 {written} 筆（累計 {stock_rows} 筆）")
            else:
                log.info(f"    本段無資料")
            time.sleep(0.1)  # 額外緩衝，避免觸發速率限制

        total_rows += stock_rows
        log.info(f"[{i}/{len(STOCK_LIST)}] {code} 完成：+{stock_rows} 筆  累計 {total_rows} 筆")

    conn.close()
    api.logout()
    log.info(f"全部完成！共寫入 {total_rows} 筆分K資料，儲存於 {DB_PATH}")


if __name__ == "__main__":
    main()
