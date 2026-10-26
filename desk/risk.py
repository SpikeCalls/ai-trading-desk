"""Seat 4: the risk engine. Plain Python. No model touches this file. Ever.

It decides whether a trade happens and how big it is. It cannot be argued with,
which is the entire point.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from config import EXITS, MIN_SCORE, RISK


@dataclass
class Account:
    equity: float
    day_pnl: float
    open_positions: int


def in_quiet_hours(now: datetime | None = None) -> bool:
    start, end = RISK["quiet_hours"]
    h = (now or datetime.now()).hour
    return start <= h < end if start < end else (h >= start or h < end)


def check_token_trade(thesis, account: Account, liquidity_usd: float,
                      now: datetime | None = None) -> tuple[bool, float, str]:
    """Return (approved, ticket_usd, reason)."""
    if account.day_pnl <= -RISK["max_daily_loss_pct"] * account.equity:
        return False, 0.0, "daily loss limit hit, desk halted until tomorrow"
    if in_quiet_hours(now):
        return False, 0.0, "quiet hours, no new entries"
    if thesis.verdict != "valid_setup":
        return False, 0.0, f"analyst verdict: {thesis.verdict}"
    if thesis.score < MIN_SCORE:
        return False, 0.0, f"score {thesis.score} < {MIN_SCORE}"
    if account.open_positions >= RISK["max_open_positions"]:
        return False, 0.0, "max open positions"

    by_risk = RISK["max_risk_per_trade"] * account.equity / EXITS["stop_pct"]
    by_size = RISK["max_position_pct"] * account.equity
    by_pool = RISK["max_pool_share"] * liquidity_usd
    ticket = round(min(by_risk, by_size, by_pool), 2)
    if ticket < RISK["min_ticket_usd"]:
        return False, 0.0, f"ticket ${ticket} below fee floor ${RISK['min_ticket_usd']}"
    return True, ticket, "approved"


# ---------- stocks (Alpaca paper) ----------
MAX_STOCK_POSITION_PCT = 0.05
ALLOWED_SYMBOLS = {"AAPL", "MSFT", "NVDA", "SPY", "QQQ"}


def check_stock_trade(thesis, account: Account, price: float) -> tuple[bool, int, str]:
    if account.day_pnl <= -RISK["max_daily_loss_pct"] * account.equity:
        return False, 0, "daily loss limit hit"
    if thesis.symbol.upper() not in ALLOWED_SYMBOLS:
        return False, 0, f"{thesis.symbol} not on the allowed list"
    if thesis.action.lower() == "hold":
        return False, 0, "model recommends no trade"
    if thesis.action.lower() == "sell":
        return False, 0, "long-only desk"
    if account.open_positions >= 5:
        return False, 0, "max open positions"
    if thesis.confidence.lower() != "high":   # enum casing is not guaranteed
        return False, 0, "only high-confidence theses trade"
    if thesis.stop_loss >= price or thesis.stop_loss <= 0:
        return False, 0, "stop must sit below entry for a long"
    stop_distance = price - thesis.stop_loss
    qty = int(min(RISK["max_risk_per_trade"] * account.equity / stop_distance,
                  MAX_STOCK_POSITION_PCT * account.equity / price))
    if qty < 1:
        return False, 0, "position too small after sizing"
    return True, qty, "approved"
