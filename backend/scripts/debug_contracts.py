"""
印出合約的 category 分布，幫助找出過濾條件。
"""
import os
from pathlib import Path
from collections import Counter
import shioaji as sj
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

api = sj.Shioaji(simulation=True)
api.login(
    api_key=os.environ["SHIOAJI_API_KEY"],
    secret_key=os.environ["SHIOAJI_SECRET_KEY"],
    contracts_timeout=30000,
)

tse = list(api.Contracts.Stocks.TSE)
print(f"TSE 總數: {len(tse)}")

# 印出 category 的分布
cats = Counter(c.category for c in tse)
print("\nTSE category 分布（前20）:")
for cat, count in cats.most_common(20):
    print(f"  category={cat!r:10} 共 {count} 支")

# 印出幾個範例看看
print("\n範例（前10筆）:")
for c in tse[:10]:
    print(f"  code={c.code}, name={c.name}, category={c.category}, unit={c.unit}")

api.logout()
