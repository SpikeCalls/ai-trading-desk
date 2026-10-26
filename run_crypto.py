"""The shift: one loop that runs the five seats in order, every minute, forever.

    python run_crypto.py            paper trading (default)
    python run_crypto.py --shadow   journal + alerts only, no paper fills
    python run_crypto.py --once     one cycle, then exit (good for testing)

Each pass is more expensive than the one before it, so each one has to kill harder:
  scanner (free) -> chain facts (RPC) -> analyst (paid) -> risk engine (code) -> paper fill
"""
from __future__ import annotations

import argparse
import time

import requests

from config import CYCLE_SECONDS
from desk import analyst, chain, scanner
from desk.broker import PaperBroker
from desk.ops import Bench, alert, journal, killed, load_env
from desk.risk import Account, check_token_trade

CHAIN_BUDGET = 8      # RPC fact checks per cycle
ANALYST_BUDGET = 3    # Claude calls per cycle: caps the bill no matter what the market does


def manage_positions(broker: PaperBroker, bench: Bench, s: requests.Session):
    for mint in list(broker.s["positions"]):
        sig = broker.exit_signal(mint, scanner.quote(mint, s))
        if sig:
            fraction, reason = sig
            price = broker.s["positions"][mint]["last"]
            fill = broker.sell(mint, fraction, price, reason)
            journal("exit", **fill)
            if "pnl_usd" in fill:
                bench.sit(mint, "exited")                     # no revenge re-entry
            alert(f"EXIT {fill['symbol']} {int(fraction * 100)}% | {reason}"
                  + (f" | pnl ${fill['pnl_usd']}" if "pnl_usd" in fill else ""))


def cycle(broker: PaperBroker, bench: Bench, s: requests.Session, shadow: bool) -> dict:
    stats = {"seen": 0, "benched": 0, "free": 0, "chain": 0, "analyst": 0, "risk": 0, "entries": 0}
    manage_positions(broker, bench, s)

    chain_left, analyst_left = CHAIN_BUDGET, ANALYST_BUDGET
    tokens = scanner.new_tokens(s)
    tokens.sort(key=lambda t: t["volume_h1"] / max(t["mcap_usd"], 1), reverse=True)

    for t in tokens:
        stats["seen"] += 1
        if t["mint"] in broker.s["positions"] or bench.benched(t["mint"]):
            stats["benched"] += 1
            continue

        if (k := scanner.free_kill(t)):                       # pass 1: free
            bench.sit(t["mint"], k)
            stats["free"] += 1
            continue
        if chain_left <= 0 or analyst_left <= 0:
            break                                             # out of budget, not out of ideas

        try:                                                  # pass 2: chain facts
            f = chain.facts(t["mint"], s)
        except Exception as e:
            journal("error", stage="chain", mint=t["mint"], error=str(e))
            continue                                          # missing is missing, not a pass
        chain_left -= 1
        if (k := chain.chain_kill(f)):
            bench.sit(t["mint"], k)
            journal("reject", stage="chain", mint=t["mint"], symbol=t["symbol"], reason=k, facts=f)
            stats["chain"] += 1
            continue

        links = scanner.socials(t["mint"], s)                 # pass 3: analyst
        try:
            th = analyst.analyze_token(t, f, links)
        except Exception as e:
            journal("error", stage="analyst", mint=t["mint"], error=str(e))
            continue
        analyst_left -= 1

        acct = Account(equity=broker.equity(), day_pnl=broker.day_pnl(),
                       open_positions=broker.open_count())
        ok, ticket, reason = check_token_trade(th, acct, t["liquidity_usd"])   # pass 4: code
        journal("decision", mint=t["mint"], symbol=t["symbol"], token=t, facts=f,
                links=links, thesis=th.model_dump(), approved=ok, ticket_usd=ticket,
                reason=reason, shadow=shadow)
        if not ok:
            bench.sit(t["mint"], th.verdict if th.verdict != "valid_setup" else "score")
            stats["analyst" if th.verdict != "valid_setup" else "risk"] += 1
            continue

        flags = "; ".join(th.red_flags[:2]) or "none"
        alert(f"VALID SETUP ${t['symbol']} score {th.score}/10 | ticket ${ticket}\n"
              f"mcap ${t['mcap_usd']:,.0f} liq ${t['liquidity_usd']:,.0f} "
              f"top10 {f['top_10_pct']:.1%}\nred flags: {flags}\n"
              f"invalidation: {th.invalidation}\n"
              f"https://pump.fun/coin/{t['mint']}\n"
              f"https://dexscreener.com/solana/{t['mint']}")
        if not shadow:                                        # pass 5: paper fill
            fill = broker.buy(t["mint"], t["symbol"], ticket, t["price_usd"])
            journal("entry", **fill)
        stats["entries"] += 1

    journal("cycle", **stats, equity=broker.equity(), day_pnl=broker.day_pnl())
    return stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shadow", action="store_true")
    ap.add_argument("--once", action="store_true")
    args = ap.parse_args()
    load_env()
    broker, bench, s = PaperBroker(), Bench(), requests.Session()
    while True:
        if killed():
            for mint in list(broker.s["positions"]):
                fill = broker.sell(mint, 1.0, broker.s["positions"][mint]["last"], "kill switch")
                journal("exit", **fill)
            alert("KILL file found. All paper positions closed. Desk stopped.")
            return
        try:
            stats = cycle(broker, bench, s, args.shadow)
            print(f"cycle {stats} equity ${broker.equity()}")
        except Exception as e:
            journal("error", stage="cycle", error=str(e))
            print(f"cycle failed: {e}")
        if args.once:
            return
        time.sleep(CYCLE_SECONDS)


if __name__ == "__main__":
    main()
