from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class Symbol(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str = Field(index=True, unique=True)


class Bot(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)


class SpotTrade(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str = Field(index=True, description="币种，比如 BTCUSDT 或 BTC")
    side: str = Field(description="BUY 或 SELL")
    quantity: float = Field(description="数量（正数）")
    price: float = Field(description="成交单价")
    fee: float = Field(default=0.0, description="手续费数值（与 fee_currency 对应）")
    fee_currency: str = Field(default="quote", description="手续费计价：base 或 quote")
    traded_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    note: Optional[str] = Field(default=None)


class ContractBot(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    bot_name: Optional[str] = Field(default=None, index=True, description="机器人名称")
    symbol: str = Field(index=True)
    profit: float = Field(description="该机器人本次总利润，正负皆可")
    closed_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    note: Optional[str] = Field(default=None)


class Investment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    currency: str = Field(description="USDT 或 MYR")
    amount: float = Field(description="投入金额，正负皆可")
    invested_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    note: Optional[str] = Field(default=None)


class InvestmentPair(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    amount_usdt: float = Field(default=0.0)
    amount_myr: float = Field(default=0.0)
    invested_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    note: Optional[str] = Field(default=None)
