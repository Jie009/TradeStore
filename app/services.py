from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable

from .models import SpotTrade


@dataclass
class SymbolState:
    quantity: float = 0.0
    cost_basis_total: float = 0.0
    realized_pnl: float = 0.0
    last_trade_at: None | object = None
    last_buy_price: float = 0.0
    total_gross_profit: float = 0.0

    @property
    def average_cost(self) -> float:
        if self.quantity <= 0:
            return 0.0
        return self.cost_basis_total / self.quantity

    @property
    def source_price(self) -> float:
        """源头价 = 手上总共的量 × 最近的买价"""
        return self.quantity * self.last_buy_price

    @property
    def cost_price(self) -> float:
        """成本价 = (源头价 - 总毛利率) / 总持有的量"""
        if self.quantity <= 0:
            return 0.0
        return (self.source_price - self.total_gross_profit) / self.quantity


def compute_spot_summary(trades: Iterable[SpotTrade]):
    states: dict[str, SymbolState] = defaultdict(SymbolState)
    for t in sorted(trades, key=lambda x: x.traded_at):
        state = states[t.symbol]
        state.last_trade_at = t.traded_at
        fee = t.fee or 0.0
        fee_currency = (t.fee_currency or "quote").lower()
        if t.side.upper() == "BUY":
            # 记录最近的买价
            state.last_buy_price = t.price

            if fee_currency == "base":
                # fee reduces received base quantity
                net_qty = t.quantity - fee
                if net_qty < 0:
                    net_qty = 0.0
                total_quote = t.quantity * t.price  # quote spent ignoring base-fee
                state.quantity += net_qty
                state.cost_basis_total += total_quote
            else:
                # fee in quote increases spent amount
                total_quote = t.quantity * t.price + fee
                state.quantity += t.quantity
                state.cost_basis_total += total_quote
        elif t.side.upper() == "SELL":
            # 毛利率 = (当前的卖价 - 最近的买价) × 当前的卖量
            gross_profit = (t.price - state.last_buy_price) * t.quantity
            state.total_gross_profit += gross_profit

            avg = state.average_cost
            proceeds = t.quantity * t.price
            # fees on sell assumed in quote (even if base specified, treat as quote impact)
            proceeds -= fee
            realized = proceeds - avg * t.quantity
            state.realized_pnl += realized
            state.quantity -= t.quantity
            if state.quantity < 0:
                state.quantity = 0.0
                state.cost_basis_total = 0.0
            else:
                state.cost_basis_total -= avg * t.quantity
        else:
            raise ValueError("Invalid side, expected BUY or SELL")

    return states
