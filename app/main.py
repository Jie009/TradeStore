from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Depends, Query, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import select

from .database import init_db, get_session
from .models import SpotTrade, ContractBot, Symbol, Bot, Investment, InvestmentPair
from .schemas import (
    SpotTradeCreate,
    SpotTradeRead,
    ContractBotCreate,
    ContractBotRead,
    SpotOverallSummary,
    SpotSymbolSummary,
    SymbolCreate,
    SymbolRead,
    BotCreate,
    BotRead,
    BotsSummary,
    InvestmentCreate,
    InvestmentRead,
    InvestmentPairCreate,
    InvestmentPairRead,
)
from .services import compute_spot_summary

app = FastAPI(title="交易记录")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/bots", response_class=HTMLResponse)
async def bots(request: Request):
    return templates.TemplateResponse("bots.html", {"request": request})


@app.get("/assets", response_class=HTMLResponse)
async def assets_page(request: Request):
    return templates.TemplateResponse("assets.html", {"request": request})


@app.get("/calc", response_class=HTMLResponse)
async def calc_page(request: Request):
    return templates.TemplateResponse("calculator.html", {"request": request})


# Symbols
@app.get("/api/symbols", response_model=list[SymbolRead])
def list_symbols(session=Depends(get_session)):
    rows = session.exec(select(Symbol).order_by(Symbol.symbol.asc())).all()
    return [SymbolRead(id=r.id, symbol=r.symbol) for r in rows]


@app.post("/api/symbols", response_model=SymbolRead)
def create_symbol(payload: SymbolCreate, session=Depends(get_session)):
    sym = payload.symbol.upper().strip()
    exists = session.exec(select(Symbol).where(Symbol.symbol == sym)).first()
    if exists:
        return SymbolRead(id=exists.id, symbol=exists.symbol)
    row = Symbol(symbol=sym)
    session.add(row)
    session.commit()
    session.refresh(row)
    return SymbolRead(id=row.id, symbol=row.symbol)


# Bots
@app.get("/api/bots", response_model=list[BotRead])
def list_bots(session=Depends(get_session)):
    rows = session.exec(select(Bot).order_by(Bot.name.asc())).all()
    return [BotRead(id=r.id, name=r.name) for r in rows]


@app.post("/api/bots", response_model=BotRead)
def create_bot(payload: BotCreate, session=Depends(get_session)):
    name = payload.name.strip()
    exists = session.exec(select(Bot).where(Bot.name == name)).first()
    if exists:
        return BotRead(id=exists.id, name=exists.name)
    row = Bot(name=name)
    session.add(row)
    session.commit()
    session.refresh(row)
    return BotRead(id=row.id, name=row.name)


# Spot trades
@app.post("/api/spot_trades", response_model=SpotTradeRead)
def create_spot_trade(payload: SpotTradeCreate, session=Depends(get_session)):
    used_amount_mode = payload.amount_quote is not None and (
        payload.quantity is None or payload.quantity == 0
    )
    quantity = payload.quantity
    if used_amount_mode:
        if payload.price <= 0:
            raise ValueError("price must be > 0 when using amount_quote")
        quantity = (payload.amount_quote or 0.0) / payload.price
    if quantity is None or quantity <= 0:
        raise ValueError("quantity must be positive")
    if payload.fee is not None:
        fee = payload.fee
    else:
        fee_rate = 0.001
        if payload.side.upper() == "BUY":
            if used_amount_mode:
                gross_quote = quantity * payload.price
                fee = gross_quote * fee_rate
            else:
                fee = quantity * fee_rate
        else:
            proceeds = quantity * payload.price
            fee = proceeds * fee_rate
    fee_currency = (
        "quote" if (payload.side.upper() == "SELL" or used_amount_mode) else "base"
    )
    trade = SpotTrade(
        symbol=payload.symbol.upper(),
        side=payload.side.upper(),
        quantity=quantity,
        price=payload.price,
        fee=fee,
        fee_currency=fee_currency,
        traded_at=payload.traded_at or datetime.utcnow(),
        note=payload.note,
    )
    session.add(trade)
    session.commit()
    session.refresh(trade)
    return SpotTradeRead(
        id=trade.id,
        symbol=trade.symbol,
        side=trade.side,
        quantity=trade.quantity,
        price=trade.price,
        fee=trade.fee,
        fee_currency=trade.fee_currency,
        traded_at=trade.traded_at,
        note=trade.note,
    )


@app.get("/api/spot_trades", response_model=list[SpotTradeRead])
def list_spot_trades(
    symbol: Optional[str] = Query(default=None), session=Depends(get_session)
):
    stmt = select(SpotTrade)
    if symbol:
        stmt = stmt.where(SpotTrade.symbol == symbol.upper())
    stmt = stmt.order_by(SpotTrade.traded_at.desc())
    rows = session.exec(stmt).all()
    return [
        SpotTradeRead(
            id=r.id,
            symbol=r.symbol,
            side=r.side,
            quantity=r.quantity,
            price=r.price,
            fee=r.fee,
            fee_currency=r.fee_currency,
            traded_at=r.traded_at,
            note=r.note,
        )
        for r in rows
    ]


@app.delete("/api/spot_trades/{trade_id}")
def delete_spot_trade(trade_id: int, session=Depends(get_session)):
    row = session.get(SpotTrade, trade_id)
    if not row:
        raise HTTPException(status_code=404, detail="Trade not found")
    session.delete(row)
    session.commit()
    return {"ok": True}


# Contract bots
@app.post("/api/contract_bots", response_model=ContractBotRead)
def create_contract_bot(payload: ContractBotCreate, session=Depends(get_session)):
    row = ContractBot(
        symbol=payload.symbol.upper(),
        profit=payload.profit,
        closed_at=payload.closed_at or datetime.utcnow(),
        note=payload.note,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return ContractBotRead(
        id=row.id,
        symbol=row.symbol,
        profit=row.profit,
        closed_at=row.closed_at,
        note=row.note,
    )


@app.get("/api/contract_bots", response_model=list[ContractBotRead])
def list_contract_bots(session=Depends(get_session)):
    rows = session.exec(
        select(ContractBot).order_by(ContractBot.closed_at.desc())
    ).all()
    return [
        ContractBotRead(
            id=r.id,
            symbol=r.symbol,
            profit=r.profit,
            closed_at=r.closed_at,
            note=r.note,
        )
        for r in rows
    ]


@app.delete("/api/contract_bots/{bot_id}")
def delete_contract_bot(bot_id: int, session=Depends(get_session)):
    row = session.get(ContractBot, bot_id)
    if not row:
        raise HTTPException(status_code=404, detail="Bot record not found")
    session.delete(row)
    session.commit()
    return {"ok": True}


@app.get("/api/summary/spot", response_model=SpotOverallSummary)
def summary_spot(
    symbol: Optional[str] = Query(default=None), session=Depends(get_session)
):
    stmt = select(SpotTrade)
    if symbol:
        stmt = stmt.where(SpotTrade.symbol == symbol.upper())
    trades = session.exec(stmt).all()
    states = compute_spot_summary(trades).items()
    symbol_summaries: list[SpotSymbolSummary] = []
    total_cost_value = 0.0
    total_realized = 0.0
    for sym, s in sorted(states, key=lambda kv: kv[0]):
        cost_value = s.average_cost * s.quantity
        symbol_summaries.append(
            SpotSymbolSummary(
                symbol=sym,
                position_quantity=s.quantity,
                average_cost=s.average_cost,
                position_cost_value=cost_value,
                realized_pnl=s.realized_pnl,
                last_trade_at=s.last_trade_at,
            )
        )
        total_cost_value += cost_value
        total_realized += s.realized_pnl
    return SpotOverallSummary(
        symbols=symbol_summaries,
        total_position_cost_value=total_cost_value,
        total_realized_pnl=total_realized,
    )


@app.get("/api/summary/bots", response_model=BotsSummary)
def bots_summary(session=Depends(get_session)):
    rows = session.exec(select(ContractBot)).all()
    total = sum(r.profit for r in rows)
    by = {}
    for r in rows:
        by[r.symbol] = by.get(r.symbol, 0.0) + r.profit
    by_list = sorted(by.items())
    return BotsSummary(total_profit=total, by_symbol=by_list)


# Investments (single currency entries)
@app.post("/api/investments", response_model=InvestmentRead)
def create_investment(payload: InvestmentCreate, session=Depends(get_session)):
    row = Investment(
        currency=payload.currency.upper(),
        amount=payload.amount,
        invested_at=payload.invested_at or datetime.utcnow(),
        note=payload.note,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return InvestmentRead(
        id=row.id,
        currency=row.currency,
        amount=row.amount,
        invested_at=row.invested_at,
        note=row.note,
    )


@app.get("/api/investments", response_model=list[InvestmentRead])
def list_investments(session=Depends(get_session)):
    rows = session.exec(
        select(Investment).order_by(Investment.invested_at.desc())
    ).all()
    return [
        InvestmentRead(
            id=r.id,
            currency=r.currency,
            amount=r.amount,
            invested_at=r.invested_at,
            note=r.note,
        )
        for r in rows
    ]


# Investment Pairs
@app.post("/api/investment_pairs", response_model=InvestmentPairRead)
def create_investment_pair(payload: InvestmentPairCreate, session=Depends(get_session)):
    row = InvestmentPair(
        amount_usdt=payload.amount_usdt,
        amount_myr=payload.amount_myr,
        invested_at=payload.invested_at or datetime.utcnow(),
        note=payload.note,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return InvestmentPairRead(
        id=row.id,
        amount_usdt=row.amount_usdt,
        amount_myr=row.amount_myr,
        invested_at=row.invested_at,
        note=row.note,
    )


@app.get("/api/investment_pairs", response_model=list[InvestmentPairRead])
def list_investment_pairs(session=Depends(get_session)):
    rows = session.exec(
        select(InvestmentPair).order_by(InvestmentPair.invested_at.desc())
    ).all()
    return [
        InvestmentPairRead(
            id=r.id,
            amount_usdt=r.amount_usdt,
            amount_myr=r.amount_myr,
            invested_at=r.invested_at,
            note=r.note,
        )
        for r in rows
    ]


@app.delete("/api/investment_pairs/{pair_id}")
def delete_investment_pair(pair_id: int, session=Depends(get_session)):
    row = session.get(InvestmentPair, pair_id)
    if not row:
        raise HTTPException(status_code=404, detail="Investment pair not found")
    session.delete(row)
    session.commit()
    return {"ok": True}


@app.get("/api/summary/overall")
def overall_summary(session=Depends(get_session)):
    # spot realized pnl only (不把持仓成本计入总资产)
    spot_rows = session.exec(select(SpotTrade)).all()
    spot_states = compute_spot_summary(spot_rows)
    total_realized_pnl = sum(s.realized_pnl for s in spot_states.values())

    # bots profits (USDT侧)
    bot_total = sum(r.profit for r in session.exec(select(ContractBot)).all())

    # investments (single)
    invests = session.exec(select(Investment)).all()
    usdt_invest_single = sum(i.amount for i in invests if i.currency.upper() == "USDT")
    myr_invest = sum(i.amount for i in invests if i.currency.upper() == "MYR")

    # pairs
    pairs = session.exec(select(InvestmentPair)).all()
    pair_usdt = sum(p.amount_usdt for p in pairs)
    pair_myr = sum(p.amount_myr for p in pairs)

    # totals without conversion: 仅 总投入(USDT) + 机器人利润 + 现货已实现盈亏
    invest_usdt_total = usdt_invest_single + pair_usdt
    invest_myr_total = myr_invest + pair_myr
    pair_usdt_total = invest_usdt_total + bot_total + total_realized_pnl

    return {
        "spot_realized_pnl": total_realized_pnl,
        "bots_profit": bot_total,
        "invest_usdt": invest_usdt_total,
        "invest_myr": invest_myr_total,
        "total_assets_pair": {"USDT": pair_usdt_total, "MYR": invest_myr_total},
    }
