from fastapi import APIRouter
from pydantic import BaseModel
from ..services.backtest_engine import run_backtest
from ..strategies.ma_cross import MACrossStrategy
from ..strategies.rsi_strategy import RSIStrategy
from ..strategies.macd_strategy import MACDStrategy

router = APIRouter(prefix="/api/v1/backtest", tags=["backtest"])

_STRATEGIES = [MACrossStrategy, RSIStrategy, MACDStrategy]
STRATEGIES   = {s.id: s for s in _STRATEGIES}


@router.get("/strategies")
def list_strategies():
    return [
        {
            "id":          s.id,
            "name":        s.name,
            "description": s.description,
            "params":      s.params_schema,
        }
        for s in _STRATEGIES
    ]


class BacktestRequest(BaseModel):
    code:        str
    start:       str
    end:         str
    strategy_id: str
    params:      dict = {}


@router.post("/run")
def run(req: BacktestRequest):
    cls = STRATEGIES.get(req.strategy_id)
    if not cls:
        return {"error": f"未知策略: {req.strategy_id}"}
    return run_backtest(req.code, req.start, req.end, cls(req.params))
