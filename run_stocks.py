"""Stocks mode: same desk, US equities, Alpaca PAPER account.

    python run_stocks.py          every 15 minutes while the market is open
    python run_stocks.py --once

The model writes a thesis. Code sizes it. Alpaca places it with the stop attached
(OTO order: the stop exists the moment the entry fills, even if this script dies).
"""
from __future__ import annotations

import argparse
import os
import time
from datetime import datetime, timedelta, timezone

from config import STOCK_CYCLE_SECONDS
from desk.analyst import analyze_stock
from desk.ops import alert, journal, killed, load_env
from desk.risk import ALLOWED_SYMBOLS, Account, check_stock_trade


def clients():
    from alpaca.data.historical import StockHistoricalDataClient
    from alpaca.data.historical.news import NewsClient
    from alpaca.trading.client import TradingClient
    key, secret = os.environ["ALPACA_API_KEY"], os.environ["ALPACA_SECRET_KEY"]
    trading = TradingClient(key, secret, paper=True)   # never change this before weeks of paper
    return trading, StockHistoricalDataClient(key, secret), NewsClient(key, secret)


def inputs(symbol: str, data, news) -> tuple[str, list[str], float]:
    from alpaca.data.requests import NewsRequest, StockBarsRequest
    from alpaca.data.timeframe import TimeFrame
    start = datetime.now(timezone.utc) - timedelta(days=5)
    bars = data.get_stock_bars(StockBarsRequest(symbol_or_symbols=symbol,
                                                timeframe=TimeFrame.Hour, start=start))
    rows = bars.data.get(symbol, [])[-30:]
    market = "\n".join(f"{b.timestamp:%m-%d %H:%M} o{b.open} h{b.high} l{b.low} c{b.close} v{int(b.volume)}"
                       for b in rows)
    price = float(rows[-1].close) if rows else 0.0
    try:
        items = news.get_news(NewsRequest(symbols=symbol, start=start, limit=10)).data.get("news", [])
        headlines = [f"{n.created_at:%m-%d %H:%M} {n.headline}. {n.summary or ''}" for n in items]
    except Exception as e:
        headlines = []
        journal("error", stage="news", symbol=symbol, error=str(e))
    return market, headlines, price


def execute(trading, thesis, qty: int):
    from alpaca.trading.enums import OrderClass, OrderSide, TimeInForce
    from alpaca.trading.requests import MarketOrderRequest, StopLossRequest
    order = MarketOrderRequest(symbol=thesis.symbol.upper(), qty=qty, side=OrderSide.BUY,
                               time_in_force=TimeInForce.DAY, order_class=OrderClass.OTO,
                               stop_loss=StopLossRequest(stop_price=round(thesis.stop_loss, 2)))
    return trading.submit_order(order_data=order)


def cycle(trading, data, news):
    if not trading.get_clock().is_open:
        return
    acct = trading.get_account()
    account = Account(equity=float(acct.equity),
                      day_pnl=float(acct.equity) - float(acct.last_equity),
                      open_positions=len(trading.get_all_positions()))
    for symbol in sorted(ALLOWED_SYMBOLS):
        market, headlines, price = inputs(symbol, data, news)
        if not price:
            continue
        th = analyze_stock(symbol, market, headlines)
        ok, qty, reason = check_stock_trade(th, account, price)
        order_id = None
        if ok:
            order_id = str(execute(trading, th, qty).id)
            account.open_positions += 1
            alert(f"PAPER BUY {qty} {symbol} @~{price} stop {th.stop_loss} | {th.entry_reason}")
        journal("stock_decision", thesis=th.model_dump(), price=price, approved=ok,
                qty=qty, reason=reason, order_id=order_id)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    args = ap.parse_args()
    load_env()
    trading, data, news = clients()
    while True:
        if killed():
            trading.close_all_positions(cancel_orders=True)
            alert("KILL file found. Alpaca paper positions closed, orders cancelled.")
            return
        try:
            cycle(trading, data, news)
        except Exception as e:
            journal("error", stage="stock_cycle", error=str(e))
            print(f"cycle failed: {e}")
        if args.once:
            return
        time.sleep(STOCK_CYCLE_SECONDS)


if __name__ == "__main__":
    main()
