from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import stocks
from .routers import backtest

app = FastAPI(title="程式交易平台")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stocks.router)
app.include_router(backtest.router)


@app.get("/")
def root():
    return {"status": "ok"}
