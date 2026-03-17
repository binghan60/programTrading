"""
快速測試單一股票的 kbars 是否能正常抓到資料。
"""
import os
import sys
from pathlib import Path
import shioaji as sj
import pandas as pd
from dotenv import load_dotenv

# 讀取環境變數
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

API_KEY = os.getenv("API_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")

if not API_KEY or not SECRET_KEY:
    print("錯誤：找不到 API_KEY 或 SECRET_KEY，請檢查 .env 檔案")
    sys.exit(1)

# 初始化 API (嘗試從環境變數決定是否使用模擬環境，預設 False)
# 如果你在 shioaji.log 看到 "Token doesn't have production permission"，請將 simulation 改為 True
simulation = os.getenv("SIMULATION", "false").upper() == "TRUE"
print(f"使用模式: {'模擬 (Simulation)' if simulation else '正式 (Production)'}")

api = sj.Shioaji(simulation=simulation)

# Login
try:
    api.login(
        api_key=API_KEY,
        secret_key=SECRET_KEY,
        fetch_contract=True  # 確保合約有被抓取
    )
    print("登入成功")
except Exception as e:
    print(f"登入失敗: {e}")
    sys.exit(1)

# 檢查合約
stock_code = "2330"
contract = api.Contracts.Stocks[stock_code]
if not contract:
    print(f"找不到 {stock_code} 的合約，嘗試搜尋...")
    # 有時候需要 fetch_contracts 或者直接搜尋
    api.fetch_contracts()
    contract = api.Contracts.Stocks[stock_code]

if not contract:
    print(f"仍然找不到 {stock_code} 的合約，請確認代碼是否正確")
    api.logout()
    sys.exit(1)

print(f"合約確認: {contract.code} {contract.name} {contract.category}")

# 測試抓取 K 線
# 1. 測試最近的資料 (比較容易有資料)
from datetime import date, timedelta
end_date = date.today().isoformat()
start_date = (date.today() - timedelta(days=7)).isoformat()

print(f"嘗試抓取最近一週資料 ({start_date} ~ {end_date})...")
kbars = api.kbars(contract=contract, start=start_date, end=end_date)

if not kbars.ts:
    # 2. 測試指定的歷史資料
    test_start = "2024-01-01"
    test_end = "2024-01-05"
    print(f"最近資料為空，嘗試抓取指定歷史區間 ({test_start} ~ {test_end})...")
    kbars = api.kbars(contract=contract, start=test_start, end=test_end)

print(f"kbars.ts 長度: {len(kbars.ts)}")

if kbars.ts:
    df = pd.DataFrame({**kbars})
    df["ts"] = pd.to_datetime(df["ts"])
    print("\n抓取成功！前幾筆資料：")
    print(df.head())
else:
    print("\n錯誤：kbars 依舊是空的！")
    print("可能原因：")
    print("1. 該帳號沒有權限抓取歷史 K 線")
    print("2. 觸發了每日抓取限額 (Shioaji 對歷史資料有每日總筆數限制)")
    print("3. 日期格式或區間不正確")
    print("4. 若使用模擬環境，歷史資料可能非常有限 (通常只有近期)")

api.logout()
