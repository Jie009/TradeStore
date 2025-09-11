from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class SymbolCreate(BaseModel):
    symbol: str


class SymbolRead(BaseModel):
    id: int
    symbol: str


class BotCreate(BaseModel):
    name: str


class BotRead(BaseModel):
    id: int
    name: str


class SpotTradeCreate(BaseModel):
    symbol: str = Field(..., description="BTCUSDT 或 BTC")
    side: str = Field(..., description="BUY 或 SELL")
    quantity: Optional[float] = None
    amount_quote: Optional[float] = None
    price: float
    fee: Optional[float] = None
    fee_mode: Optional[str] = Field(default=None, description="maker 或 taker")
    traded_at: Optional[datetime] = None
    note: Optional[str] = None

    @field_validator("side")
    @classmethod
    def normalize_side(cls, v: str) -> str:
        vv = v.upper()
        if vv not in {"BUY", "SELL"}:
            raise ValueError("side must be BUY or SELL")
        return vv


class SpotTradeRead(BaseModel):
    id: int
    symbol: str
    side: str
    quantity: float
    price: float
    fee: float
    fee_currency: str
    traded_at: datetime
    note: Optional[str]


class ContractBotCreate(BaseModel):
    symbol: str
    profit: float
    closed_at: Optional[datetime] = None
    note: Optional[str] = None


class ContractBotRead(BaseModel):
    id: int
    symbol: str
    profit: float
    closed_at: datetime
    note: Optional[str]


class BotsSummary(BaseModel):
    total_profit: float
    by_symbol: list[tuple[str, float]]


class SpotSymbolSummary(BaseModel):
    symbol: str
    position_quantity: float
    average_cost: float
    position_cost_value: float
    realized_pnl: float
    last_trade_at: Optional[datetime]


class SpotOverallSummary(BaseModel):
    symbols: list[SpotSymbolSummary]
    total_position_cost_value: float
    total_realized_pnl: float


class InvestmentCreate(BaseModel):
    currency: str
    amount: float
    invested_at: Optional[datetime] = None
    note: Optional[str] = None

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, v: str) -> str:
        vv = v.upper()
        if vv not in {"USDT", "MYR"}:
            raise ValueError("currency must be USDT or MYR")
        return vv


class InvestmentRead(BaseModel):
    id: int
    currency: str
    amount: float
    invested_at: datetime
    note: Optional[str]


class InvestmentPairCreate(BaseModel):
    amount_usdt: float = 0.0
    amount_myr: float = 0.0
    invested_at: Optional[datetime] = None
    note: Optional[str] = None


class InvestmentPairRead(BaseModel):
    id: int
    amount_usdt: float
    amount_myr: float
    invested_at: datetime
    note: Optional[str]
