"""
抓取所有上市(TSE)、上櫃(OTC) 股票的代碼、名稱，存入 SQLite stocks 表。
只需執行一次，之後更新時再跑一次即可。

使用方式：
    python scripts/fetch_metadata.py
"""

import os
import sqlite3
from pathlib import Path

import shioaji as sj
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

DB_PATH = Path(__file__).parent.parent / "data" / "stock_data.db"


def main() -> None:
    api = sj.Shioaji()
    api.login(
        api_key=os.environ["API_KEY"],
        secret_key=os.environ["SECRET_KEY"],
        contracts_timeout=30000,
    )

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS stocks (
            code     TEXT PRIMARY KEY,
            name     TEXT,
            exchange TEXT
        )
    """)

    rows = []
    for c in api.Contracts.Stocks.TSE:
        if c.category != '00':
            rows.append((c.code, c.name, "TSE"))
    for c in api.Contracts.Stocks.OTC:
        if c.category != '00':
            rows.append((c.code, c.name, "OTC"))

    conn.executemany("INSERT OR REPLACE INTO stocks VALUES (?, ?, ?)", rows)
    conn.commit()
    conn.close()
    api.logout()

    print(f"完成！儲存 {len(rows)} 支股票基本資料")


if __name__ == "__main__":
    main()
