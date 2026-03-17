"""
快速檢查 SQLite 裡的日K資料。

使用方式：
    python scripts/check_data.py          # 顯示資料庫概況
    python scripts/check_data.py 2330     # 查詢單一股票
"""

import sys
import sqlite3
from pathlib import Path

import pandas as pd

DB_PATH = Path(__file__).parent.parent / "data" / "stock_data.db"


def overview(conn: sqlite3.Connection) -> None:
    """顯示資料庫整體概況"""
    total = conn.execute("SELECT COUNT(*) FROM daily_kbars").fetchone()[0]
    stocks = conn.execute("SELECT COUNT(DISTINCT code) FROM daily_kbars").fetchone()[0]
    date_range = conn.execute("SELECT MIN(date), MAX(date) FROM daily_kbars").fetchone()

    print(f"=== 資料庫概況 ===")
    print(f"總筆數   : {total:,}")
    print(f"股票數量 : {stocks:,}")
    print(f"日期範圍 : {date_range[0]} ~ {date_range[1]}")
    print()

    # 每支股票筆數 top 10
    print("=== 資料最多的前 10 支股票 ===")
    df = pd.read_sql(
        "SELECT code, COUNT(*) as days FROM daily_kbars GROUP BY code ORDER BY days DESC LIMIT 10",
        conn,
    )
    print(df.to_string(index=False))


def query_stock(conn: sqlite3.Connection, code: str) -> None:
    """查詢單一股票的最近 20 筆日K"""
    df = pd.read_sql(
        "SELECT date, open, high, low, close, volume FROM daily_kbars WHERE code = ? ORDER BY date DESC LIMIT 20",
        conn,
        params=(code,),
    )
    if df.empty:
        print(f"找不到股票代碼 {code}")
        return

    total = conn.execute("SELECT COUNT(*) FROM daily_kbars WHERE code = ?", (code,)).fetchone()[0]
    print(f"=== {code} 最近 20 筆（共 {total} 筆）===")
    print(df.to_string(index=False))


def main() -> None:
    if not DB_PATH.exists():
        print(f"找不到資料庫：{DB_PATH}")
        print("請先執行 fetch_kbars.py 抓取資料")
        return

    conn = sqlite3.connect(DB_PATH)

    if len(sys.argv) > 1:
        query_stock(conn, sys.argv[1])
    else:
        overview(conn)

    conn.close()


if __name__ == "__main__":
    main()
