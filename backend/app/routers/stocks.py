from fastapi import APIRouter, Query
from ..database import get_conn
import pandas as pd

router = APIRouter(prefix="/api/v1/stocks", tags=["stocks"])


@router.get("")
def list_stocks(q: str = Query(default="", description="搜尋代號或名稱")):
    """回傳『已有日K資料』的股票清單"""
    conn = get_conn()
    if q:
        rows = conn.execute(
            """
            SELECT s.code, s.name, s.exchange, 1 as has_data
            FROM stocks s
            WHERE (s.code LIKE ? OR s.name LIKE ?)
              AND EXISTS (SELECT 1 FROM daily_kbars d WHERE d.code = s.code)
            ORDER BY s.code
            """,
            (f"{q}%", f"%{q}%"),
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT s.code, s.name, s.exchange, 1 as has_data
            FROM stocks s
            WHERE EXISTS (SELECT 1 FROM daily_kbars d WHERE d.code = s.code)
            ORDER BY s.code
            """
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def check_uptrend(df: pd.DataFrame) -> bool:
    """
    實作 HH/HL (Higher High, Higher Low) 多頭結構判定
    1. 將最近 60 根 K 線切為 3 段 (每段 20 根)
    2. 找出每段的高點 (High) 與低點 (Low)
    3. 判定是否為高低點持續墊高
    """
    if len(df) < 60:
        return False
        
    # 取最近 60 根
    recent_60 = df.tail(60)
    
    # 切成 3 個區塊 (每塊 20 天)
    chunk_size = 20
    chunks = [recent_60.iloc[i:i+chunk_size] for i in range(0, 60, chunk_size)]
    
    # 取得各區塊的高低點
    highs = [c['high'].max() for c in chunks]
    lows = [c['low'].min() for c in chunks]
    
    # HH: 第3段高 > 第2段高 > 第1段高
    is_hh = highs[2] > highs[1] > highs[0]
    
    # HL: 第3段低 > 第2段低 > 第1段低
    is_hl = lows[2] > lows[1] > lows[0]
    
    # 多頭結構: HH 且 HL
    # 加上一點寬鬆條件：最新收盤價不能跌破最近一段的低點
    current_close = df.iloc[-1]['close']
    is_not_broken = current_close > lows[2]
    
    return is_hh and is_hl and is_not_broken


@router.get("/screener/uptrend")
def screen_uptrend():
    """選股大師：篩選出符合 HH/HL 多頭趨勢結構的股票"""
    conn = get_conn()
    # 修正：加上別名 s 以配合 WHERE EXISTS 內的 s.code
    stocks_rows = conn.execute(
        "SELECT code, name, exchange FROM stocks s WHERE EXISTS (SELECT 1 FROM daily_kbars d WHERE d.code = s.code)"
    ).fetchall()
    
    result = []
    for s in stocks_rows:
        code = s['code']
        kbars_rows = conn.execute(
            """
            SELECT high, low, close FROM daily_kbars 
            WHERE code = ? 
            ORDER BY date DESC LIMIT 60
            """,
            (code,)
        ).fetchall()
        
        if len(kbars_rows) < 60:
            continue
            
        df = pd.DataFrame([dict(r) for r in kbars_rows]).iloc[::-1].reset_index(drop=True)
        
        if check_uptrend(df):
            result.append({
                "code": s["code"],
                "name": s["name"],
                "exchange": s["exchange"],
                "has_data": True
            })
            
    conn.close()
    return result


@router.get("/{code}/kbars")
def get_kbars(
    code: str,
    start: str = Query(default="2024-01-01"),
    end: str = Query(default="2099-12-31"),
):
    """回傳指定股票的日K資料"""
    conn = get_conn()
    rows = conn.execute(
        """
        SELECT date, open, high, low, close, volume
        FROM daily_kbars
        WHERE code = ? AND date BETWEEN ? AND ?
        ORDER BY date
        """,
        (code, start, end),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
