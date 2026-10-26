"""Seat 5a: execution. Paper only for crypto.

There is deliberately no live Solana execution in this repo: no private key,
no signing, no seed phrase anywhere. When the desk approves a token it alerts
you, and YOU click in your own terminal. That signature is the last check.
"""
from __future__ import annotations

import json
import time
from datetime import date
from pathlib import Path

from config import EXITS, PAPER

LEDGER = Path("paper_ledger.json")


class PaperBroker:
    def __init__(self, path: Path = LEDGER):
        self.path = path
        if path.exists():
            self.s = json.loads(path.read_text())
        else:
            eq = PAPER["starting_equity_usd"]
            self.s = {"cash": eq, "positions": {}, "day": str(date.today()), "day_start": eq,
                      "closed": []}
        self._roll_day()

    # ---------- state ----------
    def _save(self):
        self.path.write_text(json.dumps(self.s, indent=1))

    def _roll_day(self):
        if self.s["day"] != str(date.today()):
            self.s["day"], self.s["day_start"] = str(date.today()), self.equity()
            self._save()

    def equity(self, marks: dict[str, float] | None = None) -> float:
        marks = marks or {}
        held = sum(p["qty"] * marks.get(m, p["last"]) for m, p in self.s["positions"].items())
        return round(self.s["cash"] + held, 2)

    def day_pnl(self) -> float:
        return round(self.equity() - self.s["day_start"], 2)

    def open_count(self) -> int:
        return len(self.s["positions"])

    # ---------- orders ----------
    def buy(self, mint: str, symbol: str, ticket_usd: float, price: float) -> dict:
        fill = price * (1 + PAPER["slippage_pct"])
        fee = ticket_usd * PAPER["fee_pct"]
        qty = (ticket_usd - fee) / fill
        self.s["cash"] -= ticket_usd
        self.s["positions"][mint] = {"symbol": symbol, "qty": qty, "entry": fill,
                                     "last": fill, "opened": time.time(),
                                     "cost": ticket_usd, "half_taken": False}
        self._save()
        return {"side": "buy", "mint": mint, "qty": qty, "fill": fill, "fee": fee}

    def sell(self, mint: str, fraction: float, price: float, reason: str) -> dict:
        p = self.s["positions"][mint]
        qty = p["qty"] * fraction
        fill = price * (1 - PAPER["slippage_pct"])
        gross = qty * fill
        fee = gross * PAPER["fee_pct"]
        self.s["cash"] += gross - fee
        p["qty"] -= qty
        p["proceeds"] = p.get("proceeds", 0.0) + gross - fee
        out = {"side": "sell", "mint": mint, "symbol": p["symbol"], "qty": qty,
               "fill": fill, "fee": fee, "reason": reason}
        if fraction >= 1 or p["qty"] <= 1e-12:
            pnl = round(p["proceeds"] - p["cost"], 2)
            out["pnl_usd"] = pnl
            self.s["closed"].append({"mint": mint, "symbol": p["symbol"], "pnl_usd": pnl,
                                     "reason": reason, "closed": time.time()})
            del self.s["positions"][mint]
        self._save()
        return out

    # ---------- exits: pure rules, applied every cycle ----------
    def exit_signal(self, mint: str, q: dict | None, now: float | None = None) -> tuple[float, str] | None:
        """Return (fraction_to_sell, reason) or None. No model, no conversation."""
        sig = self._exit_signal(mint, q, now)
        self._save()
        return sig

    def _exit_signal(self, mint, q, now):
        p = self.s["positions"][mint]
        now = now or time.time()
        held_min = (now - p["opened"]) / 60
        if q is None:
            return (1.0, "no quote, cannot measure, close")
        price = q["price_usd"]
        p["last"] = price
        if price <= p["entry"] * (1 - EXITS["stop_pct"]):
            return (1.0, f"stop -{int(EXITS['stop_pct'] * 100)}%")
        if not p["half_taken"] and price >= p["entry"] * EXITS["take_half_at"]:
            p["half_taken"] = True
            return (0.5, f"take half at {EXITS['take_half_at']}x")
        if held_min >= EXITS["volume_decay_min_minutes"] and q["volume_h24"] > 0:
            ratio = q["volume_h6"] / (q["volume_h24"] / 4)
            if ratio < EXITS["volume_decay_ratio"]:
                return (1.0, f"volume decay {ratio:.2f}")
        if held_min >= EXITS["max_hold_hours"] * 60:
            return (1.0, "max hold time")
        return None
