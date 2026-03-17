# 程式交易平台

## 專案目標
使用 Claude 協助建立一個程式交易平台，整合永豐金證券 Shioaji API。

### 開發階段規劃
1. **Phase 1 - 資料收集**：用 Shioaji 抓取歷史股票日K資料，儲存至本地 SQLite
2. **Phase 2 - 策略回測**：撰寫交易策略並回測，比較績效
3. **Phase 3 - 即時交易**：串接 FastAPI + Vue 3 前後端，執行即時下單

## 技術棧
- **後端**：Python (FastAPI)
- **前端**：Vue 3 + Vite
- **交易 API**：永豐金證券 Shioaji
- **本地資料庫**：SQLite（儲存歷史 K 線資料）
- **資料分析**：pandas
- **回測套件**：backtesting.py

## 專案結構（規劃中）
```
programTrading/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── routers/
│   │   └── services/
│   ├── data/
│   │   └── stock_data.db      # SQLite 本地歷史資料
│   ├── scripts/
│   │   └── fetch_kbars.py     # 抓取歷史日K的獨立腳本
│   ├── strategies/            # 回測策略
│   ├── requirements.txt
│   └── .env                   # 憑證（不可 commit）
├── frontend/
│   ├── src/
│   ├── package.json
│   └── vite.config.js
└── sample/           # 官方範例，僅供參考，不要修改
    └── server/src/
        ├── llms.txt       # Shioaji API 摘要文件
        └── llms-full.txt  # Shioaji API 完整文件
```

## Shioaji API 參考
- 摘要文件：`sample/server/src/llms.txt`
- 完整文件：`sample/server/src/llms-full.txt`
- 線上文件：https://sinotrade.github.io/llms-full.txt

### 歷史 K 線 API 重點
```python
# 抓取日K資料
kbars = api.kbars(
    contract=api.Contracts.Stocks["2330"],
    start="2020-03-02",   # 歷史資料最早從此日期開始
    end="2024-01-01",
)
import pandas as pd
df = pd.DataFrame({**kbars})
df.ts = pd.to_datetime(df.ts)
```
- 回傳欄位：`ts`, `Open`, `High`, `Low`, `Close`, `Volume`, `Amount`
- **速率限制**：5 秒內最多 50 次 kbars 查詢，批次抓取多支股票時需加 throttle

## 憑證與環境變數
- 永豐金帳號、密碼、API token 一律存放在 `backend/.env`
- **絕對不可以 commit `.env` 檔案**
- 範例格式（`backend/.env.example`）：
  ```
  SHIOAJI_API_KEY=your_api_key
  SHIOAJI_SECRET_KEY=your_secret_key
  SHIOAJI_PERSON_ID=your_person_id
  SHIOAJI_PASSWORD=your_password
  ```

## 開發慣例
- 程式碼變數、函式名稱使用英文（snake_case）
- 註解可使用中文
- API 路由統一以 `/api/v1/` 開頭
- 前後端分離，後端預設跑 `http://localhost:8000`，前端跑 `http://localhost:5173`

## 注意事項
- `sample/` 資料夾是取得股價跟下單&前端頁面範例，只用來參考，不要在裡面新增或修改程式碼
- 實作交易功能時，優先使用模擬模式（simulation mode）測試，避免真實下單錯誤
- 批次抓取歷史資料時，注意速率限制，每次查詢後加 `time.sleep(0.1)` 避免被封鎖
